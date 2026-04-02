"""D4 (Fresh Element Solo) 设备实现"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any
from urllib.parse import quote

from .base import PetkitDevice, DeviceType, DeviceCapabilities, DeviceEntityConfig

_LOGGER = logging.getLogger(__name__)


class D4Device(PetkitDevice):
    """D4 (Fresh Element Solo) 喂食器设备.
    
    这是目前支持的主要设备型号。
    """
    
    @property
    def device_type(self) -> DeviceType:
        return DeviceType.D4
    
    @property
    def model_name(self) -> str:
        return "Fresh Element Solo"
    
    @property
    def capabilities(self) -> DeviceCapabilities:
        return DeviceCapabilities(
            supports_schedule=True,
            supports_manual_feed=True,
            supports_feeding_history=True,
            supports_food_level=True,
            supports_camera=False,
            supports_desiccant=True,
            supports_voice=False,
            supports_calibration=True,
            supports_wifi_info=True,
            supports_real_amount_total=True,
            supports_plan_amount_total=True,
            supports_add_amount_total=True,
            supports_plan_real_amount_total=True,
        )
    
    @property
    def entity_config(self) -> DeviceEntityConfig:
        return DeviceEntityConfig(
            sensors=[
                "device_name",
                "device_id",
                "last_feeding",
                "last_amount",
                "today_count",
                "feeding_schedule",
                "feeding_history",
            ],
            stat_sensors=[
                "real_amount_total",
                "plan_amount_total",
                "add_amount_total",
                "plan_real_amount_total",
            ],
            wifi_sensors=[
                "wifi_ssid",
                "wifi_rsq",
            ],
            binary_sensors=[
                "online",
            ],
            buttons=[
                "refresh",
                "manual_feed",
            ],
            switches=[
                "light_mode",
                "food_warn",
                "feed_notify",
                "manual_lock",
            ],
            numbers=[
                "feed_amount",
            ],
        )
    
    def _get_device_id(self) -> int:
        return int(self._device_data.id)
    
    def _get_device_type_id(self) -> int:
        device_nfo = getattr(self._device_data, "device_nfo", None)
        return getattr(device_nfo, "type", 11) if device_nfo else 11
    
    def _parse_time_to_seconds(self, time_str: str) -> int:
        parts = time_str.split(":")
        hours = int(parts[0]) if len(parts) >= 1 else 0
        minutes = int(parts[1]) if len(parts) >= 2 else 0
        return hours * 3600 + minutes * 60
    
    async def _save_feed_plan(
        self,
        feed_daily_list: list,
        api_client: Any,
    ) -> None:
        headers = await api_client.get_session_id()
        await api_client.req.request(
            method="POST",
            url="d4/saveFeed",
            data={
                "deviceId": self._get_device_id(),
                "feedDailyList": json.dumps(feed_daily_list),
            },
            headers=headers,
        )
    
    async def save_feed(
        self,
        days: list[int],
        items: list[dict],
        api_client: Any,
    ) -> bool:
        """保存喂食计划（批量）."""
        # 1. 转换时间格式并排序
        today_items = []
        for item in items:
            time_seconds = self._parse_time_to_seconds(item["time"])
            today_items.append({
                "time": time_seconds,
                "amount": item.get("amount", 10),
                "name": item.get("name", ""),
                "enabled": item.get("enabled", True),
            })
        
        # 2. 按时间排序
        today_items.sort(key=lambda x: x.get("time", 0))
        
        # 3. 为每个指定的周天构建计划
        feed_daily_list = [
            self._build_feed_daily_list(day, today_items)
            for day in days
        ]
        
        # 4. 调用 API 保存
        await self._save_feed_plan(feed_daily_list, api_client)
        
        _LOGGER.info(
            "保存喂食计划成功: 周%s，共%d项",
            ",".join(map(str, days)),
            len(items)
        )
        return True
    
    def _build_feed_daily_list(
        self,
        day: int,
        items: list,
    ) -> dict:
        items_data = []
        total_amount = 0
        
        for item in items:
            amount = item.get("amount", 0)
            total_amount += amount
            time_seconds = item.get("time", 0)
            is_first = len(items_data) == 0
            enabled = item.get("enabled", True)
            
            items_data.append({
                "amount": amount,
                "amount1": 0,
                "amount2": 0,
                "deviceId": self._get_device_id() if is_first else 0,
                "deviceType": self._get_device_type_id() if is_first else 0,
                "id": time_seconds,
                "name": item.get("name", ""),
                "petAmount": [],
                "time": time_seconds,
                "suspended": 0 if enabled else 1,
            })
        
        return {
            "count": len(items_data),
            "items": items_data,
            "repeats": str(day),
            "suspended": 0,
            "totalAmount": total_amount,
            "totalAmount1": 0,
            "totalAmount2": 0,
        }
    
    async def remove_feeding_item(
        self,
        day: int,
        item_id: str,
        api_client: Any,
        sync_all_days: bool = True,
        existing_feed_daily_list: list | None = None,
    ) -> bool:
        raw_item_id = item_id.lstrip("s") if item_id.startswith("s") else item_id
        
        today_items = []
        if existing_feed_daily_list:
            for daily_list in existing_feed_daily_list:
                if str(daily_list.get("repeats", "")) == str(day):
                    today_items = [
                        {
                            "time": item.get("time", 0),
                            "amount": item.get("amount", 0),
                            "name": item.get("name", ""),
                        }
                        for item in daily_list.get("items", [])
                    ]
                    break
        
        new_today_items = [
            item for item in today_items
            if str(item.get("time", "")) != raw_item_id
        ]
        
        if len(new_today_items) == len(today_items):
            _LOGGER.warning("未找到要删除的计划项: %s", item_id)
            return False
        
        if sync_all_days:
            feed_daily_list = [
                self._build_feed_daily_list(target_day, new_today_items)
                for target_day in range(1, 8)
            ]
        else:
            feed_daily_list = list(existing_feed_daily_list or [])
            for daily_list in feed_daily_list:
                if str(daily_list.get("repeats", "")) == str(day):
                    daily_list["items"] = [
                        {
                            "amount": item.get("amount"),
                            "amount1": 0,
                            "amount2": 0,
                            "deviceId": 0 if idx > 0 else self._get_device_id(),
                            "deviceType": 0 if idx > 0 else self._get_device_type_id(),
                            "id": item.get("time"),
                            "name": item.get("name", ""),
                            "petAmount": [],
                            "time": item.get("time"),
                        }
                        for idx, item in enumerate(new_today_items)
                    ]
                    daily_list["totalAmount"] = sum(item.get("amount", 0) for item in new_today_items)
                    break
        
        await self._save_feed_plan(feed_daily_list, api_client)
        _LOGGER.info("删除喂食计划成功: %s", item_id)
        return True
    
    async def toggle_feeding_item(
        self,
        day: int,
        item_id: str,
        enabled: bool,
        api_client: Any,
    ) -> bool:
        today = int(datetime.now().strftime("%Y%m%d"))
        headers = await api_client.get_session_id()
        
        if enabled:
            await api_client.req.request(
                method="POST",
                url=f"d4/restoreDailyFeed?id={item_id}&deviceId={self._get_device_id()}&day={today}",
                headers=headers,
            )
            _LOGGER.info("恢复喂食计划: 周%d %s", day, item_id)
        else:
            await api_client.req.request(
                method="POST",
                url=f"d4/removeDailyFeed?id={item_id}&deviceId={self._get_device_id()}&day={today}",
                headers=headers,
            )
            _LOGGER.info("禁用喂食计划: 周%d %s", day, item_id)
        
        return True
    
    async def manual_feed(
        self,
        amount: int,
        api_client: Any,
    ) -> bool:
        from ..pypetkitapi.command import FeederCommand
        
        try:
            result = await api_client.send_api_request(
                device_id=self._get_device_id(),
                action=FeederCommand.MANUAL_FEED,
                setting={"amount": amount},
            )
            
            if result:
                _LOGGER.info("手动出粮成功: %dg", amount)
            else:
                _LOGGER.warning("手动出粮失败: %dg", amount)
            
            return result
        except Exception as err:
            _LOGGER.error("手动出粮失败: %s", err, exc_info=True)
            return False
    
    async def update_setting(
        self,
        key: str,
        value: int,
        api_client: Any,
    ) -> bool:
        from ..pypetkitapi.command import DeviceCommand
        
        try:
            result = await api_client.send_api_request(
                device_id=self._get_device_id(),
                action=DeviceCommand.UPDATE_SETTING,
                setting={key: value},
            )
            
            if result:
                _LOGGER.info("更新设备设置成功: %s = %d", key, value)
            else:
                _LOGGER.warning("更新设备设置失败: %s = %d", key, value)
            
            return result
        except Exception as err:
            _LOGGER.error("更新设备设置失败: %s", err, exc_info=True)
            return False