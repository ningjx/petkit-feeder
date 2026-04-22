"""传感器实体."""

from __future__ import annotations

import logging
from datetime import datetime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .pypetkitapi.feeder_container import Feeder

from .const import DOMAIN
from .coordinator import PetkitDataUpdateCoordinator
from .entities import PetkitSensorEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置传感器实体."""
    coordinator: PetkitDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = [
        PetkitDeviceNameSensor(coordinator, config_entry),
        PetkitDeviceIdSensor(coordinator, config_entry),
        # PetkitFoodLevelSensor(coordinator, config_entry),  # 暂不启用
        PetkitLastFeedingSensor(coordinator, config_entry),
        PetkitLastAmountSensor(coordinator, config_entry),
        PetkitTodayCountSensor(coordinator, config_entry),
        PetkitFeedingScheduleSensor(coordinator, config_entry),
        PetkitFeedingRecordsSensor(coordinator, config_entry),
    ]
    
    # 添加喂食统计传感器（如果设备支持）
    device = coordinator.data.get("device_info") if coordinator.data else None
    if device and hasattr(device, "state") and device.state and hasattr(device.state, "feed_state"):
        feed_state = device.state.feed_state
        # 检查是否有喂食统计数据
        if hasattr(feed_state, "real_amount_total") and feed_state.real_amount_total is not None:
            entities.append(PetkitRealAmountTotalSensor(coordinator, config_entry))
        if hasattr(feed_state, "plan_amount_total") and feed_state.plan_amount_total is not None:
            entities.append(PetkitPlanAmountTotalSensor(coordinator, config_entry))
        if hasattr(feed_state, "add_amount_total") and feed_state.add_amount_total is not None:
            entities.append(PetkitAddAmountTotalSensor(coordinator, config_entry))
        if hasattr(feed_state, "plan_real_amount_total") and feed_state.plan_real_amount_total is not None:
            entities.append(PetkitPlanRealAmountTotalSensor(coordinator, config_entry))
    
    # 添加 WIFI 传感器（如果设备有 WIFI 信息）
    if device and hasattr(device, "state") and device.state and hasattr(device.state, "wifi") and device.state.wifi:
        if hasattr(device.state.wifi, "ssid") and device.state.wifi.ssid:
            entities.append(PetkitWifiSsidSensor(coordinator, config_entry))
        if hasattr(device.state.wifi, "rsq") and device.state.wifi.rsq is not None:
            entities.append(PetkitWifiRsqSensor(coordinator, config_entry))
    
    async_add_entities(entities)


class PetkitSensorBase(PetkitSensorEntity):
    """小佩传感器基类."""

    def __init__(
        self,
        coordinator: PetkitDataUpdateCoordinator,
        config_entry,
    ) -> None:
        """初始化传感器."""
        super().__init__(coordinator, config_entry)
        
        _LOGGER.debug(
            "[PetkitFeeder] Sensor initialized: entity_id=%s, unique_id=%s, device_id=%s, translation_key=%s",
            self.entity_id,
            self._attr_unique_id,
            self._device_id,
            self.translation_key,
        )

    def _get_device(self) -> Feeder | None:
        """获取设备数据."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("device_info")


class PetkitDeviceNameSensor(PetkitSensorBase):
    """设备名称传感器."""

    _attr_translation_key = "device_name"
    _attr_icon = "mdi:tag"

    @property
    def native_value(self) -> str | None:
        """返回设备名称."""
        device = self._get_device()
        if not device:
            return None
        return getattr(device, "name", None)


class PetkitDeviceIdSensor(PetkitSensorBase):
    """设备ID传感器."""

    _attr_translation_key = "device_id"
    _attr_icon = "mdi:identifier"

    @property
    def native_value(self) -> str | None:
        """返回设备ID."""
        device = self._get_device()
        if not device:
            return None
        return str(getattr(device, "id", None))


class PetkitFoodLevelSensor(PetkitSensorBase):
    """粮量传感器."""

    _attr_translation_key = "food_level"
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = "measurement"
    _attr_icon = "mdi:bowl"

    @property
    def native_value(self) -> int | None:
        """返回当前粮量."""
        device = self._get_device()
        if not device:
            return None

        # 优先使用库中提供的属性（兼容未来版本）
        if hasattr(device, "desiccant_left_percent"):
            return device.desiccant_left_percent
        if hasattr(device, "food_level"):
            return device.food_level

        # 当前 SOLO 设备上没有粮量百分比，退化为根据状态判断：1=有粮，0=无粮
        state = getattr(device, "state", None)
        food_flag = getattr(state, "food", None) if state is not None else None

        if food_flag is None:
            return None

        # 约定：有粮=100%，无粮=0%
        return 100 if food_flag else 0


class PetkitLastFeedingSensor(PetkitSensorBase):
    """最后喂食时间传感器."""

    _attr_translation_key = "last_feeding"
    _attr_device_class = "timestamp"
    _attr_icon = "mdi:clock-outline"

    @property
    def native_value(self) -> datetime | None:
        """返回最后喂食时间（从喂食历史获取最新已执行的记录）."""
        device = self._get_device()
        if not device:
            return None
        
        device_records = getattr(device, "device_records", None)
        if not device_records:
            return None
        
        feed_records = getattr(device_records, "feed", None)
        if not feed_records:
            return None
        
        # 找到最新的已执行喂食记录
        latest_completed_at = None
        
        for record in feed_records:  # RecordsType
            items = getattr(record, "items", [])
            for item in items:  # RecordsItems
                is_executed = getattr(item, "is_executed", 0)
                if is_executed != 1:
                    continue
                
                state = getattr(item, "state", None)
                if not state:
                    continue
                
                completed_at = getattr(state, "completed_at", None)
                if completed_at and (latest_completed_at is None or completed_at > latest_completed_at):
                    latest_completed_at = completed_at
        
        if not latest_completed_at:
            return None
        
        # 解析 ISO 时间并返回 datetime 对象
        try:
            dt = datetime.fromisoformat(latest_completed_at.replace("Z", "+00:00"))
            return dt
        except (ValueError, TypeError):
            return None


class PetkitLastAmountSensor(PetkitSensorBase):
    """最后喂食量传感器."""

    _attr_translation_key = "last_amount"
    _attr_native_unit_of_measurement = "g"
    _attr_state_class = "measurement"
    _attr_icon = "mdi:scale"

    @property
    def native_value(self) -> int | None:
        """返回最后喂食量（从喂食历史获取最新已执行的记录的实际出粮量）."""
        device = self._get_device()
        if not device:
            return None
        
        device_records = getattr(device, "device_records", None)
        if not device_records:
            return None
        
        feed_records = getattr(device_records, "feed", None)
        if not feed_records:
            return None
        
        # 找到最新的已执行喂食记录
        latest_item = None
        latest_completed_at = None
        
        for record in feed_records:  # RecordsType
            items = getattr(record, "items", [])
            for item in items:  # RecordsItems
                is_executed = getattr(item, "is_executed", 0)
                if is_executed != 1:
                    continue
                
                state = getattr(item, "state", None)
                if not state:
                    continue
                
                completed_at = getattr(state, "completed_at", None)
                if completed_at and (latest_completed_at is None or completed_at > latest_completed_at):
                    latest_completed_at = completed_at
                    latest_item = item
        
        if not latest_item:
            return None
        
        # 获取实际出粮量
        state = getattr(latest_item, "state", None)
        if state:
            real_amount = getattr(state, "real_amount", None)
            if real_amount is not None:
                return real_amount
        
        # 如果没有实际出粮量，返回计划出粮量
        return getattr(latest_item, "amount", None)


class PetkitTodayCountSensor(PetkitSensorBase):
    """今日喂食次数传感器."""

    _attr_translation_key = "today_count"
    _attr_state_class = "total_increasing"
    _attr_icon = "mdi:numeric"

    @property
    def native_value(self) -> int | None:
        """返回今日喂食次数."""
        device = self._get_device()
        if not device:
            return None
        # 从 pypetkitapi 的 Feeder 对象获取今日喂食次数（如果库未来提供）
        if hasattr(device, "today_feeding_count"):
            return device.today_feeding_count

        # 当前版本可以从状态里的 feed_state.times 估算今日喂食次数
        state = getattr(device, "state", None)
        feed_state = getattr(state, "feed_state", None) if state is not None else None
        times = getattr(feed_state, "times", None) if feed_state is not None else None

        return times


class PetkitFeedingScheduleSensor(PetkitSensorBase):
    """喂食计划传感器."""

    _attr_translation_key = "feeding_schedule"
    _attr_icon = "mdi:calendar-clock"

    @property
    def native_value(self) -> str:
        """返回下次喂食时间."""
        device = self._get_device()
        if not device:
            return "离线"
        
        multi_feed_item = getattr(device, "multi_feed_item", None)
        if not multi_feed_item:
            return "无计划"
        
        feed_daily_list = getattr(multi_feed_item, "feed_daily_list", None)
        if not feed_daily_list:
            return "无计划"
        
        now = datetime.now()
        current_weekday = now.weekday() + 1  # Monday=1, Sunday=7
        current_time = now.strftime("%H:%M")
        current_seconds = now.hour * 3600 + now.minute * 60
        today_date = int(now.strftime("%Y%m%d"))  # 今天的日期，如 20260404
        
        today_items = []
        for daily_list in feed_daily_list:
            repeats = getattr(daily_list, "repeats", None)
            if repeats == current_weekday:
                items = getattr(daily_list, "items", [])
                for item in items:
                    time_seconds = getattr(item, "time", 0)
                    name = getattr(item, "name", "")
                    amount = getattr(item, "amount", 0)
                    hours = time_seconds // 3600
                    minutes = (time_seconds % 3600) // 60
                    time_str = f"{hours:02d}:{minutes:02d}"
                    
                    device_records = getattr(device, "device_records", None)
                    is_executed = False
                    if device_records:
                        feed_records = getattr(device_records, "feed", None)
                        if feed_records:
                            for record in feed_records:
                                # 只处理今天的记录
                                record_day = getattr(record, "day", None)
                                if record_day != today_date:
                                    continue
                                    
                                record_items = getattr(record, "items", [])
                                for ri in record_items:
                                    ri_time = getattr(ri, "time", None)
                                    ri_state = getattr(ri, "state", None)
                                    if ri_time == time_seconds and ri_state:
                                        is_executed = getattr(ri_state, "completed_at", None) is not None
                                        break
                    
                    if not is_executed and time_seconds > current_seconds:
                        today_items.append((time_seconds, time_str, name, amount))
        
        today_items.sort(key=lambda x: x[0])
        
        if today_items:
            _, time_str, name, amount = today_items[0]
            return f"{time_str} {name} {amount}g"
        
        return "今日无待喂食"

    @property
    def extra_state_attributes(self) -> dict:
        """返回喂食计划的详细数据（周一到周日）."""
        device = self._get_device()
        if not device:
            return {}

        multi_feed_item = getattr(device, "multi_feed_item", None)
        if not multi_feed_item:
            return {}

        feed_daily_list = getattr(multi_feed_item, "feed_daily_list", None)
        if not feed_daily_list:
            return {}

        weekday_names = {
            1: "周一",
            2: "周二",
            3: "周三",
            4: "周四",
            5: "周五",
            6: "周六",
            7: "周日",
        }

        schedule = {}

        for daily_list in feed_daily_list:
            repeats = getattr(daily_list, "repeats", None)
            suspended = getattr(daily_list, "suspended", 0)
            if not repeats or repeats < 1 or repeats > 7:
                continue

            weekday_name = weekday_names[repeats]
            items = getattr(daily_list, "items", [])
            schedule_items = []

            for item in items:
                time_seconds = getattr(item, "time", None)
                amount = getattr(item, "amount", 0)
                name = getattr(item, "name", "")
                item_id = getattr(item, "id", None)

                if time_seconds is not None:
                    hours = time_seconds // 3600
                    minutes = (time_seconds % 3600) // 60
                    time_str = f"{hours:02d}:{minutes:02d}"

                    schedule_items.append({
                        "id": item_id,
                        "time": time_str,
                        "name": name,
                        "amount": amount,
                    })

            schedule[weekday_name] = {
                "suspended": suspended,
                "items": schedule_items,
            }

        return {
            "schedule": schedule,
        }


class PetkitFeedingRecordsSensor(PetkitSensorBase):
    """喂食记录传感器."""

    _attr_translation_key = "feeding_records"
    _attr_icon = "mdi:history"

    @property
    def native_value(self) -> str:
        """返回本周最新喂食时间."""
        device = self._get_device()
        if not device:
            return "离线"
        
        device_records = getattr(device, "device_records", None)
        if not device_records:
            return "无记录"
        
        latest_item = None
        latest_completed_at = None
        
        feed_records = getattr(device_records, "feed", None)
        if feed_records:
            for record in feed_records:
                items = getattr(record, "items", [])
                for item in items:
                    state = getattr(item, "state", None)
                    if state:
                        completed_at = getattr(state, "completed_at", None)
                        if completed_at and (latest_completed_at is None or completed_at > latest_completed_at):
                            latest_completed_at = completed_at
                            latest_item = item
        
        if not latest_completed_at or not latest_item:
            return "暂无喂食"
        
        try:
            dt = datetime.fromisoformat(latest_completed_at.replace("Z", "+00:00"))
            time_seconds = getattr(latest_item, "time", 0)
            hours = time_seconds // 3600
            minutes = (time_seconds % 3600) // 60
            time_str = f"{hours:02d}:{minutes:02d}"
            name = getattr(latest_item, "name", "")
            real_amount = getattr(latest_item.state, "real_amount", 0) if latest_item.state else 0
            return f"{time_str} {name} {real_amount}g"
        except (ValueError, TypeError):
            return "时间未知"

    @property
    def extra_state_attributes(self) -> dict:
        """返回本周喂食记录的详细数据."""
        device = self._get_device()
        if not device:
            return {}
        
        device_records = getattr(device, "device_records", None)
        if not device_records:
            return {}
        
        today_str = datetime.now().strftime("%Y%m%d")
        
        records = {}
        week_plan_amount = 0
        week_real_amount = 0
        week_completed_count = 0
        today_plan_amount = 0
        today_real_amount = 0
        today_count = 0
        today_completed_count = 0
        
        feed_records = getattr(device_records, "feed", None)
        if feed_records:
            for record in feed_records:
                day = getattr(record, "day", None)
                if not day:
                    continue
                    
                items = getattr(record, "items", [])
                plan_amount = getattr(record, "plan_amount", 0) or 0
                real_amount = getattr(record, "real_amount", 0) or 0
                add_amount = getattr(record, "add_amount", 0) or 0
                times = getattr(record, "times", 0) or 0
                
                day_str = str(day)
                date_key = f"{day_str[:4]}-{day_str[4:6]}-{day_str[6:8]}" if len(day_str) == 8 else day_str
                
                items_list = []
                for item in items:
                    time_seconds = getattr(item, "time", 0)
                    hours = time_seconds // 3600
                    minutes = (time_seconds % 3600) // 60
                    time_str = f"{hours:02d}:{minutes:02d}"
                    
                    amount = getattr(item, "amount", 0)
                    name = getattr(item, "name", "")
                    item_id = getattr(item, "id", None)
                    src = getattr(item, "src", None)
                    status = getattr(item, "status", 0)
                    is_executed = getattr(item, "is_executed", 0) == 1
                    
                    state = getattr(item, "state", None)
                    real_amt = getattr(state, "real_amount", None) if state else None
                    completed_at = getattr(state, "completed_at", None) if state else None
                    err_code = getattr(state, "err_code", None) if state else None
                    result = getattr(state, "result", None) if state else None
                    is_completed = completed_at is not None
                    
                    items_list.append({
                        "id": item_id,
                        "time": time_str,
                        "name": name,
                        "amount": amount,
                        "src": src,
                        "status": status,
                        "is_executed": is_executed,
                        "state": {
                            "real_amount": real_amt,
                            "completed_at": completed_at,
                            "err_code": err_code,
                            "result": result,
                        } if state else None,
                    })
                    
                    if is_completed:
                        week_completed_count += 1
                
                records[date_key] = {
                    "day": day,
                    "plan_amount": plan_amount,
                    "add_amount": add_amount,
                    "real_amount": real_amount,
                    "times": times,
                    "items": items_list,
                }
                
                week_plan_amount += plan_amount
                week_real_amount += real_amount
                
                if str(day) == today_str:
                    today_plan_amount = plan_amount
                    today_real_amount = real_amount
                    today_count = len(items)
                    today_completed_count = sum(
                        1 for i in items 
                        if getattr(getattr(i, "state", None), "completed_at", None)
                    )
        
        attributes = {
            "records": records,
            "week_plan_amount": week_plan_amount,
            "week_real_amount": week_real_amount,
            "week_completed_count": week_completed_count,
            "today_plan_amount": today_plan_amount,
            "today_real_amount": today_real_amount,
            "today_count": today_count,
            "today_completed_count": today_completed_count,
        }
        
        return attributes


# ============ 新增：喂食统计传感器 ============

class PetkitRealAmountTotalSensor(PetkitSensorBase):
    """实际喂食总量传感器."""

    _attr_translation_key = "real_amount_total"
    _attr_icon = "mdi:food-drumstick"
    _attr_native_unit_of_measurement = "g"
    _attr_state_class = "total_increasing"

    @property
    def native_value(self) -> int | None:
        """返回实际喂食总量."""
        device = self._get_device()
        if not device:
            return None
        state = getattr(device, "state", None)
        if not state:
            return None
        feed_state = getattr(state, "feed_state", None)
        if not feed_state:
            return None
        return getattr(feed_state, "real_amount_total", None)


class PetkitPlanAmountTotalSensor(PetkitSensorBase):
    """计划喂食总量传感器."""

    _attr_translation_key = "plan_amount_total"
    _attr_icon = "mdi:calendar-clock"
    _attr_native_unit_of_measurement = "g"
    _attr_state_class = "total_increasing"

    @property
    def native_value(self) -> int | None:
        """返回计划喂食总量."""
        device = self._get_device()
        if not device:
            return None
        state = getattr(device, "state", None)
        if not state:
            return None
        feed_state = getattr(state, "feed_state", None)
        if not feed_state:
            return None
        return getattr(feed_state, "plan_amount_total", None)


class PetkitAddAmountTotalSensor(PetkitSensorBase):
    """手动喂食总量传感器."""

    _attr_translation_key = "add_amount_total"
    _attr_icon = "mdi:hand-front-left"
    _attr_native_unit_of_measurement = "g"
    _attr_state_class = "total_increasing"

    @property
    def native_value(self) -> int | None:
        """返回手动喂食总量."""
        device = self._get_device()
        if not device:
            return None
        state = getattr(device, "state", None)
        if not state:
            return None
        feed_state = getattr(state, "feed_state", None)
        if not feed_state:
            return None
        return getattr(feed_state, "add_amount_total", None)


class PetkitPlanRealAmountTotalSensor(PetkitSensorBase):
    """计划实际喂食总量传感器."""

    _attr_translation_key = "plan_real_amount_total"
    _attr_icon = "mdi:counter"
    _attr_native_unit_of_measurement = "g"
    _attr_state_class = "total_increasing"

    @property
    def native_value(self) -> int | None:
        """返回计划实际喂食总量."""
        device = self._get_device()
        if not device:
            return None
        state = getattr(device, "state", None)
        if not state:
            return None
        feed_state = getattr(state, "feed_state", None)
        if not feed_state:
            return None
        return getattr(feed_state, "plan_real_amount_total", None)


# ============ 新增：WIFI 信息传感器 ============

class PetkitWifiSsidSensor(PetkitSensorBase):
    """WIFI 名称传感器."""

    _attr_translation_key = "wifi_ssid"
    _attr_icon = "mdi:wifi"

    @property
    def native_value(self) -> str | None:
        """返回 WIFI 名称."""
        device = self._get_device()
        if not device:
            return None
        state = getattr(device, "state", None)
        if not state:
            return None
        wifi = getattr(state, "wifi", None)
        if not wifi:
            return None
        return getattr(wifi, "ssid", None)


class PetkitWifiRsqSensor(PetkitSensorBase):
    """WIFI 强度传感器."""

    _attr_translation_key = "wifi_rsq"
    _attr_icon = "mdi:wifi-strength-4"
    _attr_native_unit_of_measurement = "dBm"
    _attr_state_class = "measurement"

    @property
    def native_value(self) -> int | None:
        """返回 WIFI 强度."""
        device = self._get_device()
        if not device:
            return None
        state = getattr(device, "state", None)
        if not state:
            return None
        wifi = getattr(state, "wifi", None)
        if not wifi:
            return None
        return getattr(wifi, "rsq", None)
