"""传感器实体."""

from __future__ import annotations

import logging
from datetime import datetime
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .pypetkitapi.feeder_container import Feeder

from .const import DOMAIN, DEFAULT_NAME
from .coordinator import PetkitDataUpdateCoordinator

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
        PetkitLastFeedingSensor(coordinator, config_entry),
        PetkitLastAmountSensor(coordinator, config_entry),
        PetkitTodayCountSensor(coordinator, config_entry),
        PetkitFeedingScheduleSensor(coordinator, config_entry),
        PetkitFeedingHistorySensor(coordinator, config_entry),
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


class PetkitSensorBase(CoordinatorEntity, SensorEntity):
    """小佩传感器基类."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PetkitDataUpdateCoordinator,
        config_entry,
    ) -> None:
        """初始化传感器."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_{self.translation_key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": DEFAULT_NAME,
            "manufacturer": "Petkit",
            "model": "SOLO",
        }

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
        """返回当前计划名称或状态."""
        device = self._get_device()
        if not device:
            return "未知"
        
        multi_feed_item = getattr(device, "multi_feed_item", None)
        if multi_feed_item and hasattr(multi_feed_item, "is_executed"):
            return "已启用" if multi_feed_item.is_executed else "未启用"
        
        return "未知"

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

        # 周一到周日的名称映射
        weekday_names = {
            1: "monday",
            2: "tuesday",
            3: "wednesday",
            4: "thursday",
            5: "friday",
            6: "saturday",
            7: "sunday",
        }
        weekday_names_cn = {
            1: "周一",
            2: "周二",
            3: "周三",
            4: "周四",
            5: "周五",
            6: "周六",
            7: "周日",
        }

        schedule = {}
        schedule_cn = {}  # 中文版本，用于前端显示

        for daily_list in feed_daily_list:
            repeats = getattr(daily_list, "repeats", None)
            if not repeats or repeats < 1 or repeats > 7:
                continue

            weekday_key = weekday_names[repeats]
            weekday_cn = weekday_names_cn[repeats]

            items = getattr(daily_list, "items", [])
            schedule_items = []
            schedule_items_cn = []

            for item in items:
                time_seconds = getattr(item, "time", None)
                amount = getattr(item, "amount", None)
                name = getattr(item, "name", "")
                item_id_raw = getattr(item, "id", None)
                item_id = f"s{item_id_raw}" if item_id_raw and not str(item_id_raw).startswith("s") else item_id_raw

                if time_seconds is not None:
                    hours = time_seconds // 3600
                    minutes = (time_seconds % 3600) // 60
                    time_str = f"{hours:02d}:{minutes:02d}"

                    schedule_items.append(
                        {
                            "id": item_id,
                            "time": time_str,
                            "portions": amount if amount is not None else 0,
                            "name": name if name else "",
                        }
                    )
                    schedule_items_cn.append(
                        {
                            "id": item_id,
                            "time": time_str,
                            "portions": amount if amount is not None else 0,
                            "name": name if name else "",
                        }
                    )

            schedule[weekday_key] = schedule_items
            schedule_cn[weekday_cn] = schedule_items_cn

        return {
            "schedule": schedule,  # 英文键名，便于程序处理
            "schedule_cn": schedule_cn,  # 中文键名，便于前端显示
            "is_executed": getattr(multi_feed_item, "is_executed", False),
        }


class PetkitFeedingHistorySensor(PetkitSensorBase):
    """喂食历史传感器."""

    _attr_translation_key = "feeding_history"
    _attr_icon = "mdi:history"

    @property
    def native_value(self) -> str:
        """返回最后一条喂食记录的时间."""
        device = self._get_device()
        if not device:
            return "设备离线"
        
        # 从 device_records 获取历史记录
        device_records = getattr(device, "device_records", None)
        if not device_records:
            return "设备不支持"
        
        # 获取最新的喂食记录时间
        latest_completed_at = None
        
        feed_records = getattr(device_records, "feed", None)
        if feed_records:
            for record in feed_records:  # RecordsType
                items = getattr(record, "items", [])
                for item in items:  # RecordsItems
                    state = getattr(item, "state", None)
                    if state:
                        completed_at = getattr(state, "completed_at", None)
                        if completed_at and (latest_completed_at is None or completed_at > latest_completed_at):
                            latest_completed_at = completed_at
        
        if not latest_completed_at:
            return "暂无记录"
        
        # completed_at 格式: "2026-03-10T22:00:19.000+0000"
        try:
            # 解析 ISO 格式时间
            dt = datetime.fromisoformat(latest_completed_at.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            return "时间未知"

    @property
    def extra_state_attributes(self) -> dict:
        """返回喂食历史的详细数据."""
        device = self._get_device()
        if not device:
            return {}
        
        device_records = getattr(device, "device_records", None)
        if not device_records:
            return {}
        
        today_str = datetime.now().strftime("%Y%m%d")
        
        by_date = {}
        today_plan_amount = 0
        today_real_amount = 0
        today_count = 0
        today_completed_count = 0
        
        feed_records = getattr(device_records, "feed", None)
        if feed_records:
            for record in feed_records:
                day = getattr(record, "day", None)
                items = getattr(record, "items", [])
                plan_amount = getattr(record, "plan_amount", 0)
                real_amount = getattr(record, "real_amount", 0)
                
                day_str = str(day) if day else "未知"
                date_key = f"{day_str[:4]}-{day_str[4:6]}-{day_str[6:8]}" if len(day_str) == 8 else day_str
                
                if date_key not in by_date:
                    by_date[date_key] = []
                
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
                    is_completed = completed_at is not None
                    
                    by_date[date_key].append({
                        "id": item_id,
                        "time": time_str,
                        "name": name,
                        "amount": amount,
                        "real_amount": real_amt,
                        "status": status,
                        "is_executed": is_executed,
                        "is_completed": is_completed,
                        "completed_at": completed_at,
                        "src": src,
                    })
                
                if str(day) == today_str:
                    today_plan_amount = plan_amount or 0
                    today_real_amount = real_amount or 0
                    today_count = len(items)
                    today_completed_count = sum(1 for i in items if getattr(getattr(i, "state", None), "completed_at", None))
        
        total_records = sum(len(records) for records in by_date.values())
        
        attributes = {
            "history": by_date,
            "total_records": total_records,
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
    _attr_icon = "mdi:chart-check"
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
