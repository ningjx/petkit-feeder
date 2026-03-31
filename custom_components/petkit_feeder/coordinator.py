"""数据协调器 - 负责定时刷新数据."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any
import asyncio
import socket
import types

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .pypetkitapi.client import PetKitClient
from .pypetkitapi.exceptions import PetkitAuthenticationError, PypetkitError

from .const import (
    DOMAIN,
    UPDATE_INTERVAL,
    REFRESH_MODE_AUTO,
    REFRESH_MODE_MANUAL,
    REGION_TIMEZONE_MAP,
    DEFAULT_TIMEZONE,
    PLAN_REFRESH_DELAY,
)

_LOGGER = logging.getLogger(__name__)

# 全局请求节流配置（单位：秒）
PETKIT_REQUEST_INTERVAL = 10
_rate_limit_lock: asyncio.Lock | None = None
_last_request_time: float | None = None


class PetkitDataUpdateCoordinator(DataUpdateCoordinator):
    """小佩 SOLO 数据协调器."""

    def __init__(
        self,
        hass: HomeAssistant,
        username: str,
        password: str,
        device_id: str,
        region: str = "CN",
        refresh_mode: str = REFRESH_MODE_AUTO,
        refresh_interval: int = UPDATE_INTERVAL,
    ) -> None:
        """初始化数据协调器."""
        self.hass = hass
        self._username = username
        self._password = password
        self._device_id = device_id
        self._region = region
        self._refresh_mode = refresh_mode
        self._refresh_interval = refresh_interval
        self._api: PetKitClient | None = None
        self._feed_amount: int = 10
        self._timezone: float = 8.0
        self._timezone_str: str = "Asia/Shanghai"
        self._plan_refresh_unsub: Any = None
        
        self._init_timezone()
        
        # aiohttp 会话
        self._session: aiohttp.ClientSession | None = None
        
        # API 客户端（使用 pypetkitapi 库）
        self._api: PetKitClient | None = None
        
        # 计算刷新间隔
        update_interval = (
            timedelta(seconds=refresh_interval)
            if refresh_mode == REFRESH_MODE_AUTO
            else timedelta(hours=1)  # 手动模式下设置较长的刷新间隔
        )
        
        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )

    def _init_timezone(self) -> None:
        """初始化时区设置（自动获取，优先 HA 系统时区）."""
        # 第一优先级：HA 系统时区
        ha_timezone = self.hass.config.time_zone if self.hass else None
        
        if ha_timezone:
            self._timezone_str = ha_timezone
            self._timezone = self._get_timezone_offset(ha_timezone)
            
            # 详细日志
            _LOGGER.info(
                "=== 时区初始化 ===\n"
                "来源：HA 系统时区\n"
                "时区名称：%s\n"
                "UTC 偏移：UTC%s%.1f\n"
                "当前时间：%s",
                ha_timezone,
                "+" if self._timezone >= 0 else "",
                self._timezone,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            return
        
        # 第二优先级：根据地区分配默认时区
        region_timezone = REGION_TIMEZONE_MAP.get(self._region, DEFAULT_TIMEZONE)
        self._timezone_str = region_timezone
        self._timezone = self._get_timezone_offset(region_timezone)
        
        # 详细日志
        _LOGGER.info(
            "=== 时区初始化 ===\n"
            "来源：地区默认时区（HA 系统时区未设置）\n"
            "用户地区：%s\n"
            "时区名称：%s\n"
            "UTC 偏移：UTC%s%.1f\n"
            "当前时间：%s",
            self._region,
            region_timezone,
            "+" if self._timezone >= 0 else "",
            self._timezone,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

    @staticmethod
    def _get_timezone_offset(timezone_str: str) -> float:
        """将时区字符串转换为 UTC 偏移小时数.
        
        Args:
            timezone_str: 时区名称，如 "Asia/Shanghai"
            
        Returns:
            UTC 偏移小时数，如 8.0（考虑夏令时）
        """
        try:
            import zoneinfo
            from datetime import datetime
            
            tz = zoneinfo.ZoneInfo(timezone_str)
            now = datetime.now(tz)
            offset = now.utcoffset()
            
            if offset:
                offset_hours = offset.total_seconds() / 3600
                _LOGGER.debug("时区 %s 当前偏移：UTC%s%.1f", 
                             timezone_str,
                             "+" if offset_hours >= 0 else "",
                             offset_hours)
                return offset_hours
            
            return 8.0
            
        except Exception as err:
            _LOGGER.warning("时区偏移转换失败：%s，使用默认 UTC+8", err)
            return 8.0

    async def _async_setup(self) -> None:
        """设置协调器（在初次刷新前调用）."""
        # 部分环境下 IPv6 路由不可达，会导致偶发 Network unreachable
        # 强制使用 IPv4 以避免该问题
        connector = aiohttp.TCPConnector(family=socket.AF_INET)
        self._session = aiohttp.ClientSession(connector=connector)
        self._api = PetKitClient(
            username=self._username,
            password=self._password,
            region=self._region,
            timezone=self.hass.config.time_zone or "Asia/Shanghai",
            session=self._session,
        )
        _LOGGER.debug("PetKit API 客户端初始化完成")

        # 给 pypetkitapi 的 request 方法加一个全局节流器，保证所有请求按间隔排队
        self._wrap_api_with_rate_limiter()

    def _wrap_api_with_rate_limiter(self) -> None:
        """为 PetKitClient 的 request 方法增加全局节流（排队 + 间隔）."""
        global _rate_limit_lock, _last_request_time

        if not self._api or not getattr(self._api, "req", None):
            return

        # 只初始化一次全局锁
        if _rate_limit_lock is None:
            _rate_limit_lock = asyncio.Lock()
            _last_request_time = None

        # pypetkitapi 通过 self.req.request 发送 HTTP 请求
        original_request = self._api.req.request

        async def rate_limited_request(self_req, *args, **kwargs):
            """带全局间隔的 request 包装器."""
            assert _rate_limit_lock is not None
            global _last_request_time

            async with _rate_limit_lock:
                now = asyncio.get_running_loop().time()
                if _last_request_time is not None:
                    # 距上次请求的时间差
                    delta = now - _last_request_time
                    wait_for = PETKIT_REQUEST_INTERVAL - delta
                    if wait_for > 0:
                        _LOGGER.debug(
                            "PetKit API 触发节流，等待 %.2f 秒后再发送请求", wait_for
                        )
                        await asyncio.sleep(wait_for)

                # 真正发送请求
                result = await original_request(*args, **kwargs)

                # 记录本次请求时间
                _last_request_time = asyncio.get_running_loop().time()
                return result

        # 绑定为实例方法，替换底层 req 对象的 request 方法
        self._api.req.request = types.MethodType(rate_limited_request, self._api.req)

    async def cleanup(self) -> None:
        """清理资源."""
        if self._plan_refresh_unsub:
            self._plan_refresh_unsub()
            self._plan_refresh_unsub = None
        if self._session:
            await self._session.close()
            self._session = None
            _LOGGER.debug("API 会话已关闭")

    async def _async_update_data(self) -> dict[str, Any]:
        """获取最新数据."""
        try:
            # 测试日志：打印系统时间信息
            # 系统本地时间
            local_now = datetime.now()
            # UTC 时间
            utc_now = datetime.now(timezone.utc)
            # 系统时区偏移
            local_tz_offset = datetime.now().astimezone().utcoffset()
            
            _LOGGER.debug(
                "=== 时间信息测试 ===\n"
                "系统本地时间: %s\n"
                "UTC 时间: %s\n"
                "系统时区偏移: %s\n"
                "设置的时区: UTC%s%d\n"
                "当前时区日期: %s\n"
                "当前时区时间: %s",
                local_now.strftime("%Y-%m-%d %H:%M:%S"),
                utc_now.strftime("%Y-%m-%d %H:%M:%S"),
                local_tz_offset,
                "+" if self._timezone >= 0 else "",
                self._timezone,
                self.get_current_date_str(),
                self.get_current_datetime().strftime("%Y-%m-%d %H:%M:%S"),
            )
            
            # 确保 API 客户端已初始化
            if not self._api:
                await self._async_setup()
            
            # 登录（如果需要）
            if not self._api._session:
                _LOGGER.debug("正在登录 PetKit API")
                await self._api.login()
            
            # 获取所有设备数据
            _LOGGER.debug("正在获取设备数据")
            await self._api.get_devices_data()
            
            # 从 petkit_entities 中找到我们的设备
            device_data = None
            for dev_id, device in self._api.petkit_entities.items():
                if str(dev_id) == str(self._device_id):
                    device_data = device
                    break
            
            if not device_data:
                _LOGGER.warning("未找到设备 ID: %s", self._device_id)
                # 如果没有找到指定设备，使用第一个喂食器
                for dev_id, device in self._api.petkit_entities.items():
                    from .pypetkitapi.feeder_container import Feeder
                    if isinstance(device, Feeder):
                        device_data = device
                        self._device_id = str(dev_id)
                        _LOGGER.info("使用设备 ID: %s", self._device_id)
                        break
            
            if not device_data:
                raise UpdateFailed("未找到任何喂食器设备")

            # 记录一次设备对象的可用属性，方便调试实体取值
            try:
                attrs = {
                    k: getattr(device_data, k)
                    for k in dir(device_data)
                    if not k.startswith("_")
                }
                _LOGGER.debug("设备属性快照（截断显示）：%s", {k: attrs[k] for k in list(attrs)[:20]})
            except Exception:  # 日志失败不影响正常更新
                _LOGGER.debug("无法记录设备属性快照", exc_info=True)

            # 详细打印 device_records 结构，用于分析喂食历史
            try:
                device_records = getattr(device_data, "device_records", None)
                if device_records is not None:
                    _LOGGER.debug("device_records 完整结构：%s", device_records)
                    # 尝试打印 device_records 的所有属性
                    if hasattr(device_records, "__dict__"):
                        _LOGGER.debug("device_records.__dict__: %s", device_records.__dict__)
                    # 尝试打印 device_records 的所有字段
                    record_attrs = {
                        k: getattr(device_records, k)
                        for k in dir(device_records)
                        if not k.startswith("_")
                    }
                    _LOGGER.debug("device_records 所有属性：%s", record_attrs)
                    
                    # 解析喂食历史记录
                    feeding_history = self._parse_feeding_history(device_records)
                    _LOGGER.debug("解析后的喂食历史：%s", feeding_history)
                else:
                    _LOGGER.debug("device_records 为 None，设备可能暂无历史记录")
            except Exception as e:
                _LOGGER.debug("无法记录 device_records 结构：%s", e, exc_info=True)

            _LOGGER.info("数据更新成功，设备：%s", device_data.name if hasattr(device_data, 'name') else self._device_id)
            
            self._schedule_plan_refresh(device_data)
            
            return {
                "device_info": device_data,
                "device_id": self._device_id,
            }
            
        except PetkitAuthenticationError as err:
            _LOGGER.error("认证失败：%s", err)
            raise UpdateFailed(f"认证失败：{err}") from err
        except PypetkitError as err:
            _LOGGER.error("PetKit API 请求失败：%s", err)
            raise UpdateFailed(f"API 请求失败：{err}") from err
        except Exception as err:
            _LOGGER.error("数据更新失败：%s", err)
            raise UpdateFailed(f"数据更新失败：{err}") from err

    async def async_request_refresh(self) -> None:
        """手动刷新数据."""
        _LOGGER.debug("手动刷新数据")
        await self.async_refresh()

    def _get_today_plan_times(self, device_data: Any) -> list[datetime]:
        """获取今天的喂食计划时间列表.
        
        Args:
            device_data: 设备数据对象
            
        Returns:
            今天的喂食计划时间列表（datetime 对象）
        """
        plan_times: list[datetime] = []
        
        try:
            multi_feed_item = getattr(device_data, "multi_feed_item", None)
            if not multi_feed_item:
                return plan_times
            
            feed_daily_list = getattr(multi_feed_item, "feed_daily_list", [])
            if not feed_daily_list:
                return plan_times
            
            today_weekday = self.get_current_datetime().weekday() + 1
            
            for daily_list in feed_daily_list:
                repeats = getattr(daily_list, "repeats", None)
                if repeats != today_weekday:
                    continue
                
                items = getattr(daily_list, "items", [])
                suspended = getattr(daily_list, "suspended", 0)
                if suspended:
                    continue
                
                for item in items:
                    time_seconds = getattr(item, "time", None)
                    if time_seconds is None:
                        continue
                    
                    hour = time_seconds // 3600
                    minute = (time_seconds % 3600) // 60
                    
                    now = self.get_current_datetime()
                    plan_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    plan_times.append(plan_time)
                
                break
            
            _LOGGER.debug("今天的喂食计划时间: %s", [t.strftime("%H:%M") for t in plan_times])
            
        except Exception as err:
            _LOGGER.debug("获取喂食计划时间失败: %s", err)
        
        return plan_times

    def _schedule_plan_refresh(self, device_data: Any) -> None:
        """安排计划刷新.
        
        在每条喂食计划时间 + 2分钟后刷新数据，以获取执行结果。
        
        Args:
            device_data: 设备数据对象
        """
        if self._plan_refresh_unsub:
            self._plan_refresh_unsub()
            self._plan_refresh_unsub = None
        
        plan_times = self._get_today_plan_times(device_data)
        if not plan_times:
            return
        
        now = self.get_current_datetime()
        next_refresh_time: datetime | None = None
        
        for plan_time in plan_times:
            refresh_time = plan_time + timedelta(seconds=PLAN_REFRESH_DELAY)
            
            if refresh_time > now:
                next_refresh_time = refresh_time
                break
        
        if not next_refresh_time:
            _LOGGER.debug("今天没有需要刷新的计划了")
            return
        
        _LOGGER.info(
            "计划刷新已安排: %s",
            next_refresh_time.strftime("%Y-%m-%d %H:%M:%S")
        )
        
        from homeassistant.helpers.event import async_track_point_in_time
        
        async def _plan_refresh_callback(now: datetime) -> None:
            """计划刷新回调."""
            _LOGGER.info("执行计划刷新")
            self._plan_refresh_unsub = None
            await self.async_refresh()
        
        self._plan_refresh_unsub = async_track_point_in_time(
            self.hass,
            _plan_refresh_callback,
            next_refresh_time,
        )

    def set_feed_amount(self, amount: int) -> None:
        """设置出粮量."""
        self._feed_amount = amount
        _LOGGER.debug("设置出粮量: %dg", amount)

    def get_feed_amount(self) -> int:
        """获取当前设置的出粮量."""
        return self._feed_amount

    def get_current_datetime(self) -> datetime:
        """获取当前时区的日期时间.
        
        Returns:
            当前时区的 datetime 对象
        """
        from datetime import timezone, timedelta
        
        # 创建时区对象
        tz = timezone(timedelta(hours=self._timezone))
        
        # 获取当前时间并转换到目标时区
        now = datetime.now(tz)
        
        _LOGGER.debug(
            "当前时区时间: %s (UTC%s%d)",
            now.strftime("%Y-%m-%d %H:%M:%S"),
            "+" if self._timezone >= 0 else "",
            self._timezone
        )
        
        return now

    def get_current_date_str(self) -> str:
        """获取当前时区的日期字符串.
        
        Returns:
            日期字符串，格式: YYYYMMDD
        """
        now = self.get_current_datetime()
        return now.strftime("%Y%m%d")

    def convert_utc_to_timezone(self, utc_datetime_str: str) -> str | None:
        """将 UTC 时间字符串转换为当前时区.
        
        Args:
            utc_datetime_str: UTC 时间字符串，格式如 "2026-03-12T04:00:20.000+0000"
            
        Returns:
            转换后的时区时间字符串，格式如 "2026-03-12T12:00:20.000+0800"
        """
        if not utc_datetime_str:
            return None
        
        try:
            import zoneinfo
            from datetime import datetime
            
            # 解析 UTC 时间
            utc_str = utc_datetime_str.replace("+0000", "+00:00").replace("-0000", "-00:00")
            utc_dt = datetime.fromisoformat(utc_str)
            
            # 转换到目标时区
            target_tz = zoneinfo.ZoneInfo(self._timezone_str)
            target_dt = utc_dt.astimezone(target_tz)
            
            # 格式化输出
            result = target_dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + target_dt.strftime("%z")
            
            _LOGGER.debug(
                "时间转换：%s (UTC) → %s (%s)",
                utc_datetime_str,
                result,
                self._timezone_str
            )
            
            return result
            
        except Exception as err:
            _LOGGER.debug("时区转换失败：%s, 原始时间：%s", err, utc_datetime_str)
            return utc_datetime_str

    async def manual_feed(self, amount: int | None = None) -> bool:
        """手动出粮.
        
        Args:
            amount: 出粮量（克），如果为 None 则使用已设置的值
            
        Returns:
            是否成功
        """
        from .pypetkitapi.command import FeederCommand
        
        if not self._api:
            _LOGGER.error("API 未初始化")
            return False
        
        # 获取出粮量
        feed_amount = amount if amount is not None else self._feed_amount
        
        _LOGGER.info("手动出粮: %dg", feed_amount)
        
        try:
            result = await self._api.send_api_request(
                device_id=int(self._device_id),
                action=FeederCommand.MANUAL_FEED,
                setting={"amount": feed_amount},
            )
            
            if result:
                _LOGGER.info("手动出粮成功: %dg", feed_amount)
                # 刷新数据
                await self.async_request_refresh()
            else:
                _LOGGER.warning("手动出粮失败: %dg", feed_amount)
            
            return result
            
        except Exception as err:
            _LOGGER.error("手动出粮失败: %s", err, exc_info=True)
            return False

    async def update_setting(self, key: str, value: int) -> bool:
        """更新设备设置.
        
        Args:
            key: 设置项名称 (lightMode, foodWarn, feedNotify, manualLock)
            value: 值 (0=关, 1=开)
            
        Returns:
            是否成功
        """
        from .pypetkitapi.command import DeviceCommand
        
        if not self._api:
            _LOGGER.error("API 未初始化")
            return False
        
        _LOGGER.info("更新设备设置: %s = %d", key, value)
        
        try:
            result = await self._api.send_api_request(
                device_id=int(self._device_id),
                action=DeviceCommand.UPDATE_SETTING,
                setting={key: value},
            )
            
            if result:
                _LOGGER.info("更新设备设置成功: %s = %d", key, value)
                # 刷新数据
                await self.async_request_refresh()
            else:
                _LOGGER.warning("更新设备设置失败: %s = %d", key, value)
            
            return result
            
        except Exception as err:
            _LOGGER.error("更新设备设置失败: %s", err, exc_info=True)
            return False

    def set_refresh_mode(
        self,
        refresh_mode: str,
        refresh_interval: int | None = None,
    ) -> None:
        """设置刷新模式."""
        self._refresh_mode = refresh_mode
        
        if refresh_interval is not None:
            self._refresh_interval = refresh_interval
        
        # 更新刷新间隔
        if refresh_mode == REFRESH_MODE_AUTO:
            self.update_interval = timedelta(seconds=self._refresh_interval)
            _LOGGER.info("刷新模式：定时刷新，间隔：%d 秒", self._refresh_interval)
        else:
            # 手动模式下设置较长的刷新间隔，避免频繁请求
            self.update_interval = timedelta(hours=1)
            _LOGGER.info("刷新模式：手动刷新")

    async def update_feeding_schedule(
        self,
        day: int,
        schedule_items: list[dict],
    ) -> None:
        """更新指定周几的喂食计划.
        
        Args:
            day: 1-7，周一到周日
            schedule_items: 计划项列表，每个元素包含 time（秒数）、amount（份数）、name（名称）
        """
        if not self._api:
            await self._async_setup()
        
        device = self.data.get("device_info") if self.data else None
        if not device:
            raise ValueError("设备数据不可用")
        
        multi_feed_item = getattr(device, "multi_feed_item", None)
        if not multi_feed_item:
            raise ValueError("设备不支持多日计划")
        
        feed_daily_list = getattr(multi_feed_item, "feed_daily_list", [])
        
        from .pypetkitapi.feeder_container import FeedDailyList, FeedItem
        
        new_daily_list = []
        updated = False
        
        for daily_list in feed_daily_list:
            repeats = getattr(daily_list, "repeats", None)
            if repeats == day:
                feed_items = [
                    FeedItem(
                        time=item["time"],
                        amount=item["amount"],
                        amount1=None,
                        amount2=None,
                        id=str(item["time"]),
                        name=item.get("name", ""),
                    )
                    for item in schedule_items
                ]
                new_daily = FeedDailyList(
                    items=feed_items,
                    repeats=day,
                    suspended=0,
                )
                new_daily_list.append(new_daily)
                updated = True
            else:
                new_daily_list.append(daily_list)
        
        if not updated:
            feed_items = [
                FeedItem(
                    time=item["time"],
                    amount=item["amount"],
                    amount1=None,
                    amount2=None,
                    id=str(item["time"]),
                    name=item.get("name", ""),
                )
                for item in schedule_items
            ]
            new_daily = FeedDailyList(
                items=feed_items,
                repeats=day,
                suspended=0,
            )
            new_daily_list.append(new_daily)
        
        try:
            if hasattr(device, "update_multi_feed_item"):
                await device.update_multi_feed_item(new_daily_list)
            elif hasattr(device, "set_multi_feed_item"):
                await device.set_multi_feed_item(new_daily_list)
            elif hasattr(self._api, "update_feeding_schedule"):
                await self._api.update_feeding_schedule(
                    device_id=self._device_id,
                    feed_daily_list=new_daily_list,
                )
            else:
                _LOGGER.warning(
                    "pypetkitapi 未提供更新计划的方法，尝试直接设置属性（可能不会生效）"
                )
                from .pypetkitapi.feeder_container import MultiFeedItem
                multi_feed_item.feed_daily_list = new_daily_list
                await self.async_request_refresh()
                return
        except Exception as err:
            _LOGGER.error("调用 API 更新计划失败: %s", err, exc_info=True)
            raise
        
        await self.async_request_refresh()
        _LOGGER.info("喂食计划更新成功：周%d，共%d项", day, len(schedule_items))

    async def add_feeding_item(
        self,
        day: int,
        time_str: str,
        amount: int,
        name: str = "",
        sync_all_days: bool = True,
    ) -> bool:
        """新增喂食计划项（同步一周）.
        
        Args:
            day: 1-7，周一到周日（起始天）
            time_str: 时间字符串，格式 HH:MM
            amount: 出粮量（克）
            name: 计划名称
            sync_all_days: 是否同步到一周所有天
            
        Returns:
            是否成功
        """
        if not self._api:
            _LOGGER.error("API 未初始化")
            return False
        
        device = self.data.get("device_info") if self.data else None
        if not device:
            _LOGGER.error("设备数据不可用")
            return False
        
        time_seconds = self._parse_time_to_seconds(time_str)
        
        multi_feed_item = getattr(device, "multi_feed_item", None)
        if not multi_feed_item:
            _LOGGER.error("设备不支持多日计划")
            return False
        
        feed_daily_list = list(getattr(multi_feed_item, "feed_daily_list", []))
        
        from .pypetkitapi.feeder_container import FeedDailyList, FeedItem
        
        today_items = []
        for daily_list in feed_daily_list:
            if getattr(daily_list, "repeats", None) == day:
                today_items = list(getattr(daily_list, "items", []))
                break
        
        for item in today_items:
            if getattr(item, "time", None) == time_seconds:
                _LOGGER.warning("该时间点已存在计划项: %s", time_str)
                return False
        
        new_item = FeedItem(
            time=time_seconds,
            amount=amount,
            id=str(time_seconds),
            name=name,
        )
        today_items.append(new_item)
        today_items.sort(key=lambda x: getattr(x, "time", 0))
        
        if sync_all_days:
            new_feed_daily_list = []
            for target_day in range(1, 8):
                new_daily = FeedDailyList(
                    items=[FeedItem(
                        time=getattr(item, "time"),
                        amount=getattr(item, "amount"),
                        id=str(getattr(item, "time")),
                        name=getattr(item, "name", ""),
                    ) for item in today_items],
                    repeats=target_day,
                    suspended=0,
                )
                new_feed_daily_list.append(new_daily)
            feed_daily_list = new_feed_daily_list
        else:
            for daily_list in feed_daily_list:
                if getattr(daily_list, "repeats", None) == day:
                    daily_list.items = today_items
                    break
        
        try:
            await self._save_feed_plan(feed_daily_list)
            _LOGGER.info("新增喂食计划成功: %s %dg，同步到一周", time_str, amount)
            return True
        except Exception as err:
            _LOGGER.error("新增喂食计划失败: %s", err, exc_info=True)
            return False

    async def remove_feeding_item(
        self,
        day: int,
        item_id: str,
        sync_all_days: bool = True,
    ) -> bool:
        """删除喂食计划项（同步一周）.
        
        Args:
            day: 1-7，周一到周日（起始天）
            item_id: 计划项 ID（时间秒数）
            sync_all_days: 是否同步到一周所有天
            
        Returns:
            是否成功
        """
        if not self._api:
            _LOGGER.error("API 未初始化")
            return False
        
        device = self.data.get("device_info") if self.data else None
        if not device:
            _LOGGER.error("设备数据不可用")
            return False
        
        multi_feed_item = getattr(device, "multi_feed_item", None)
        if not multi_feed_item:
            _LOGGER.error("设备不支持多日计划")
            return False
        
        feed_daily_list = list(getattr(multi_feed_item, "feed_daily_list", []))
        
        from .pypetkitapi.feeder_container import FeedDailyList, FeedItem
        
        raw_item_id = item_id.lstrip("s") if item_id.startswith("s") else item_id
        
        today_items = []
        for daily_list in feed_daily_list:
            if getattr(daily_list, "repeats", None) == day:
                today_items = list(getattr(daily_list, "items", []))
                break
        
        new_today_items = [item for item in today_items if str(getattr(item, "time", "")) != raw_item_id]
        
        if len(new_today_items) == len(today_items):
            _LOGGER.warning("未找到要删除的计划项: %s", item_id)
            return False
        
        if sync_all_days:
            new_feed_daily_list = []
            for target_day in range(1, 8):
                new_daily = FeedDailyList(
                    items=[FeedItem(
                        time=getattr(item, "time"),
                        amount=getattr(item, "amount"),
                        id=str(getattr(item, "time")),
                        name=getattr(item, "name", ""),
                    ) for item in new_today_items],
                    repeats=target_day,
                    suspended=0,
                )
                new_feed_daily_list.append(new_daily)
            feed_daily_list = new_feed_daily_list
        else:
            for daily_list in feed_daily_list:
                if getattr(daily_list, "repeats", None) == day:
                    daily_list.items = new_today_items
                    break
        
        try:
            await self._save_feed_plan(feed_daily_list)
            _LOGGER.info("删除喂食计划成功: %s，同步到一周", item_id)
            return True
        except Exception as err:
            _LOGGER.error("删除喂食计划失败: %s", err, exc_info=True)
            return False

    async def toggle_feeding_item(
        self,
        day: int,
        item_id: str,
        enabled: bool,
    ) -> bool:
        """启用/禁用喂食计划项.
        
        Args:
            day: 1-7，周一到周日
            item_id: 计划项 ID
            enabled: True 启用，False 禁用
            
        Returns:
            是否成功
        """
        from .pypetkitapi.command import FeederCommand
        
        if not self._api:
            _LOGGER.error("API 未初始化")
            return False
        
        try:
            action = FeederCommand.RESTORE_DAILY_FEED if enabled else FeederCommand.REMOVE_DAILY_FEED
            
            result = await self._api.send_api_request(
                device_id=int(self._device_id),
                action=action,
                setting={"id": item_id},
            )
            
            if result:
                await self.async_request_refresh()
                _LOGGER.info("切换喂食计划状态成功: 周%d %s %s", day, item_id, "启用" if enabled else "禁用")
            else:
                _LOGGER.warning("切换喂食计划状态失败: 周%d %s", day, item_id)
            
            return result
            
        except Exception as err:
            _LOGGER.error("切换喂食计划状态失败: %s", err, exc_info=True)
            return False

    async def update_feeding_item(
        self,
        day: int,
        item_id: str,
        time_str: str | None = None,
        amount: int | None = None,
        name: str | None = None,
        sync_all_days: bool = True,
    ) -> bool:
        """更新喂食计划项（同步一周）.
        
        Args:
            day: 1-7，周一到周日（起始天）
            item_id: 计划项 ID（时间秒数）
            time_str: 新时间（可选）
            amount: 新出粮量（可选）
            name: 新名称（可选）
            sync_all_days: 是否同步到一周所有天
            
        Returns:
            是否成功
        """
        if not self._api:
            _LOGGER.error("API 未初始化")
            return False
        
        device = self.data.get("device_info") if self.data else None
        if not device:
            _LOGGER.error("设备数据不可用")
            return False
        
        multi_feed_item = getattr(device, "multi_feed_item", None)
        if not multi_feed_item:
            _LOGGER.error("设备不支持多日计划")
            return False
        
        feed_daily_list = list(getattr(multi_feed_item, "feed_daily_list", []))
        
        from .pypetkitapi.feeder_container import FeedDailyList, FeedItem
        
        raw_item_id = item_id.lstrip("s") if item_id.startswith("s") else item_id
        
        today_items = []
        for daily_list in feed_daily_list:
            if getattr(daily_list, "repeats", None) == day:
                today_items = list(getattr(daily_list, "items", []))
                break
        
        found = False
        for i, item in enumerate(today_items):
            if str(getattr(item, "time", "")) == raw_item_id:
                found = True
                new_time = self._parse_time_to_seconds(time_str) if time_str else getattr(item, "time")
                new_amount = amount if amount is not None else getattr(item, "amount")
                new_name = name if name is not None else getattr(item, "name", "")
                today_items[i] = FeedItem(
                    time=new_time,
                    amount=new_amount,
                    id=str(new_time),
                    name=new_name,
                )
                today_items.sort(key=lambda x: getattr(x, "time", 0))
                break
        
        if not found:
            _LOGGER.warning("未找到计划项: 周%d %s", day, item_id)
            return False
        
        if sync_all_days:
            new_feed_daily_list = []
            for target_day in range(1, 8):
                new_daily = FeedDailyList(
                    items=[FeedItem(
                        time=getattr(item, "time"),
                        amount=getattr(item, "amount"),
                        id=str(getattr(item, "time")),
                        name=getattr(item, "name", ""),
                    ) for item in today_items],
                    repeats=target_day,
                    suspended=0,
                )
                new_feed_daily_list.append(new_daily)
            feed_daily_list = new_feed_daily_list
        else:
            for daily_list in feed_daily_list:
                if getattr(daily_list, "repeats", None) == day:
                    daily_list.items = today_items
                    break
        
        try:
            await self._save_feed_plan(feed_daily_list)
            _LOGGER.info("更新喂食计划成功: %s，同步到一周", item_id)
            return True
        except Exception as err:
            _LOGGER.error("更新喂食计划失败: %s", err, exc_info=True)
            return False

    async def _save_feed_plan(self, feed_daily_list: list) -> None:
        """保存喂食计划到服务器.
        
        Args:
            feed_daily_list: 喂食计划列表
        """
        if not self._api:
            raise ValueError("API 未初始化")
        
        device = self.data.get("device_info") if self.data else None
        if not device:
            raise ValueError("设备数据不可用")
        
        device_nfo = getattr(device, "device_nfo", None)
        device_type = getattr(device_nfo, "device_type", "d4") if device_nfo else "d4"
        device_type_id = getattr(device_nfo, "type", 11) if device_nfo else 11
        
        feed_list_data = []
        for daily_list in feed_daily_list:
            items = getattr(daily_list, "items", []) or []
            items_data = []
            total_amount = 0
            
            for item in items:
                amount = getattr(item, "amount", 0)
                total_amount += amount
                is_first = len(items_data) == 0
                items_data.append({
                    "amount": amount,
                    "amount1": 0,
                    "amount2": 0,
                    "deviceId": int(self._device_id) if is_first else 0,
                    "deviceType": device_type_id if is_first else 0,
                    "id": getattr(item, "time", 0),
                    "name": getattr(item, "name", ""),
                    "petAmount": [],
                    "time": getattr(item, "time", 0),
                })
            
            repeats = getattr(daily_list, "repeats", 0)
            feed_list_data.append({
                "count": len(items_data),
                "items": items_data,
                "repeats": str(repeats),
                "suspended": getattr(daily_list, "suspended", 0),
                "totalAmount": total_amount,
                "totalAmount1": 0,
                "totalAmount2": 0,
            })
        
        import json
        response = await self._api.req.request(
            method="POST",
            url=f"{device_type}/saveFeed",
            data={
                "deviceId": int(self._device_id),
                "feedDailyList": json.dumps(feed_list_data),
            },
            headers=await self._api.get_session_id(),
        )
        
        _LOGGER.debug("保存喂食计划响应: %s", response)
        await self.async_request_refresh()

    def _parse_time_to_seconds(self, time_str: str) -> int:
        """将时间字符串转换为秒数.
        
        Args:
            time_str: 时间字符串，格式 HH:MM
            
        Returns:
            从 00:00 开始的秒数
        """
        parts = time_str.split(":")
        hours = int(parts[0]) if len(parts) >= 1 else 0
        minutes = int(parts[1]) if len(parts) >= 2 else 0
        return hours * 3600 + minutes * 60

    def _parse_feeding_history(self, device_records) -> dict:
        """解析喂食历史记录.
        
        Args:
            device_records: FeederRecord 对象
            
        Returns:
            解析后的历史记录字典
            
        数据结构:
            device_records.feed = [
                RecordsType(
                    day=20260311,
                    items=[
                        RecordsItems(id='s21600', time=21600, amount=10, name='早餐', state=EventState(...), is_executed=1),
                        ...
                    ],
                    plan_amount=40,
                    real_amount=40
                )
            ]
        """
        history = {
            "feed": [],
            "eat": [],
            "total": 0,
            "by_date": {},  # 按日期分组
        }
        
        try:
            # 处理 feed 记录（计划喂食）
            feed_records = getattr(device_records, "feed", None)
            if feed_records:
                for record in feed_records:  # RecordsType
                    day = getattr(record, "day", None)
                    items = getattr(record, "items", [])
                    plan_amount = getattr(record, "plan_amount", 0)
                    real_amount = getattr(record, "real_amount", 0)
                    
                    # 遍历 items（RecordsItems）
                    for item in items:
                        item_data = self._parse_feed_item(item, day)
                        if item_data:
                            history["feed"].append(item_data)
                    
                    # 按日期汇总
                    if day:
                        day_str = str(day)
                        # 真正执行完成数量：有 state 且有 completed_at
                        completed_count = sum(
                            1 for i in items 
                            if getattr(i, "state", None) and getattr(getattr(i, "state", None), "completed_at", None)
                        )
                        history["by_date"][day_str] = {
                            "plan_amount": plan_amount,
                            "real_amount": real_amount,
                            "items_count": len(items),
                            "completed_count": completed_count,
                        }
            
            # 处理 eat 记录（实际进食）
            eat_records = getattr(device_records, "eat", None)
            if eat_records:
                for record in eat_records:
                    items = getattr(record, "items", [])
                    for item in items:
                        item_data = self._parse_eat_item(item)
                        if item_data:
                            history["eat"].append(item_data)
            
            # 按时间排序（最新的在前）
            history["feed"].sort(key=lambda x: x.get("time", 0) or 0, reverse=True)
            history["eat"].sort(key=lambda x: x.get("time", 0) or 0, reverse=True)
            history["total"] = len(history["feed"]) + len(history["eat"])
            
        except Exception as err:
            _LOGGER.debug("解析喂食历史失败：%s", err, exc_info=True)
        
        return history

    def _parse_feed_item(self, item, day: int | None = None) -> dict | None:
        """解析单条喂食记录项（RecordsItems）.
        
        Args:
            item: RecordsItems 对象
            day: 日期（从 RecordsType 继承）
            
        Returns:
            解析后的记录字典
        """
        try:
            # 获取时间（秒数，从 00:00 开始）
            time_seconds = getattr(item, "time", None)
            if time_seconds is None:
                return None
            
            # 转换为 HH:MM 格式
            hours = time_seconds // 3600
            minutes = (time_seconds % 3600) // 60
            time_str = f"{hours:02d}:{minutes:02d}"
            
            # 获取出粮量
            amount = getattr(item, "amount", 0)
            
            # 获取其他字段
            item_id = getattr(item, "id", None)
            name = getattr(item, "name", "")
            src = getattr(item, "src", None)  # 来源: 1=计划, 4=手动
            status = getattr(item, "status", None)
            is_enabled = getattr(item, "is_executed", 0) == 1  # 计划项是否有效
            
            # 构建记录字典
            record_data = {
                "id": item_id,
                "day": day,
                "time": time_seconds,
                "time_str": time_str,
                "amount": amount,
                "name": name,
                "src": src,
                "status": status,
                "is_enabled": is_enabled,
                "is_completed": False,  # 默认未完成，下面会根据 state 更新
            }
            
            # 如果有状态对象，提取更多信息
            state = getattr(item, "state", None)
            if state:
                record_data["real_amount"] = getattr(state, "real_amount", None)
                # 转换 completed_at 到用户时区
                completed_at_utc = getattr(state, "completed_at", None)
                if completed_at_utc:
                    record_data["completed_at"] = self.convert_utc_to_timezone(completed_at_utc)
                    record_data["completed_at_utc"] = completed_at_utc  # 保留原始 UTC 时间
                    record_data["is_completed"] = True  # 有 completed_at 才是真正执行完成
                else:
                    record_data["completed_at"] = None
                record_data["err_code"] = getattr(state, "err_code", None)
                record_data["result"] = getattr(state, "result", None)
            
            return record_data
            
        except Exception as err:
            _LOGGER.debug("解析喂食记录项失败：%s", err)
            return None

    def _parse_eat_item(self, item) -> dict | None:
        """解析单条进食记录项（RecordsItems）.
        
        Args:
            item: RecordsItems 对象
            
        Returns:
            解析后的记录字典
        """
        try:
            # 获取时间戳
            timestamp = getattr(item, "timestamp", None) or getattr(item, "eat_start_time", None)
            if not timestamp:
                return None
            
            # 获取进食量
            eat_weight = getattr(item, "eat_weight", None)
            
            # 获取其他字段
            item_id = getattr(item, "id", None)
            pet_id = getattr(item, "pet_id", None)
            
            return {
                "id": item_id,
                "timestamp": timestamp,
                "eat_weight": eat_weight,
                "pet_id": pet_id,
            }
            
        except Exception as err:
            _LOGGER.debug("解析进食记录项失败：%s", err)
            return None
            
            # 获取出粮量
            amount = getattr(record, "amount", None)
            if amount is None:
                amount = getattr(record, "amount1", None)
            if amount is None:
                amount = getattr(record, "amount2", None)
            
            # 获取其他字段
            event_type = getattr(record, "event_type", None)
            enum_event_type = getattr(record, "enum_event_type", "")
            pet_id = getattr(record, "pet_id", None)
            device_id = getattr(record, "device_id", None)
            status = getattr(record, "status", None)
            is_executed = getattr(record, "is_executed", None)
            
            # 构建记录字典
            record_data = {
                "type": record_type,
                "timestamp": timestamp,
                "amount": amount,
                "event_type": event_type,
                "enum_event_type": enum_event_type,
                "pet_id": pet_id,
                "device_id": device_id or self._device_id,
                "status": status,
                "is_executed": is_executed,
            }
            
            # 如果有状态对象，提取更多信息
            state = getattr(record, "state", None)
            if state:
                record_data["real_amount"] = getattr(state, "real_amount", None)
                record_data["real_amount1"] = getattr(state, "real_amount1", None)
                record_data["real_amount2"] = getattr(state, "real_amount2", None)
                record_data["err_code"] = getattr(state, "err_code", None)
                record_data["result"] = getattr(state, "result", None)
            
            return record_data
            
        except Exception as err:
            _LOGGER.debug("解析单条记录失败：%s", err)
            return None
