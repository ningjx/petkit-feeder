"""传感器实体."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

from homeassistant.components.sensor import SensorEntityDescription, SensorDeviceClass, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import PetkitDataUpdateCoordinator
from .entities import PetkitSensorEntity
from .pypetkitapi.feeder_container import Feeder

_LOGGER = logging.getLogger(__name__)


@dataclass(kw_only=True)
class PetkitSensorEntityDescription(SensorEntityDescription):
    """描述 Petkit 传感器实体."""

    value_fn: Callable[[Feeder], Any] | None = None


# 简单传感器定义
SIMPLE_SENSORS: tuple[PetkitSensorEntityDescription, ...] = (
    PetkitSensorEntityDescription(
        key="device_name",
        translation_key="device_name",
        icon="mdi:tag",
        value_fn=lambda device: getattr(device, "name", None),
    ),
    PetkitSensorEntityDescription(
        key="device_id",
        translation_key="device_id",
        icon="mdi:identifier",
        value_fn=lambda device: str(getattr(device, "id", None)),
    ),
    PetkitSensorEntityDescription(
        key="real_amount_total",
        translation_key="real_amount_total",
        icon="mdi:food-drumstick",
        native_unit_of_measurement="g",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda device: getattr(
            getattr(getattr(device, "state", None), "feed_state", None),
            "real_amount_total",
            None
        ),
    ),
    PetkitSensorEntityDescription(
        key="plan_amount_total",
        translation_key="plan_amount_total",
        icon="mdi:calendar-clock",
        native_unit_of_measurement="g",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda device: getattr(
            getattr(getattr(device, "state", None), "feed_state", None),
            "plan_amount_total",
            None
        ),
    ),
    PetkitSensorEntityDescription(
        key="add_amount_total",
        translation_key="add_amount_total",
        icon="mdi:hand-front-left",
        native_unit_of_measurement="g",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda device: getattr(
            getattr(getattr(device, "state", None), "feed_state", None),
            "add_amount_total",
            None
        ),
    ),
    PetkitSensorEntityDescription(
        key="plan_real_amount_total",
        translation_key="plan_real_amount_total",
        icon="mdi:counter",
        native_unit_of_measurement="g",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda device: getattr(
            getattr(getattr(device, "state", None), "feed_state", None),
            "plan_real_amount_total",
            None
        ),
    ),
    PetkitSensorEntityDescription(
        key="wifi_ssid",
        translation_key="wifi_ssid",
        icon="mdi:wifi",
        value_fn=lambda device: getattr(
            getattr(getattr(device, "state", None), "wifi", None),
            "ssid",
            None
        ),
    ),
    PetkitSensorEntityDescription(
        key="wifi_rsq",
        translation_key="wifi_rsq",
        icon="mdi:wifi-strength-4",
        native_unit_of_measurement="dBm",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda device: getattr(
            getattr(getattr(device, "state", None), "wifi", None),
            "rsq",
            None
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置传感器实体."""
    coordinator: PetkitDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []

    # 简单传感器
    for description in SIMPLE_SENSORS:
        entities.append(PetkitSimpleSensor(coordinator, config_entry, description))

    # 复杂传感器（保留原有实现）
    entities.append(PetkitLastFeedingSensor(coordinator, config_entry))
    entities.append(PetkitLastAmountSensor(coordinator, config_entry))
    entities.append(PetkitTodayCountSensor(coordinator, config_entry))
    entities.append(PetkitFeedingScheduleSensor(coordinator, config_entry))
    entities.append(PetkitFeedingRecordsSensor(coordinator, config_entry))

    # 检查喂食统计数据是否存在，动态添加
    device = coordinator.data.get("device_info") if coordinator.data else None
    if device and hasattr(device, "state") and device.state and hasattr(device.state, "feed_state"):
        feed_state = device.state.feed_state
        # 这些已经在 SIMPLE_SENSORS 中定义，但需要检查数据是否存在
        # 实际上我们已经在上面添加了，这里只是为了兼容原有逻辑的检查
        pass

    async_add_entities(entities)


class PetkitSimpleSensor(PetkitSensorEntity):
    """简单传感器实体."""

    entity_description: PetkitSensorEntityDescription

    def __init__(
        self,
        coordinator: PetkitDataUpdateCoordinator,
        config_entry,
        entity_description: PetkitSensorEntityDescription,
    ) -> None:
        """初始化传感器."""
        # 先设置 entity_description，再调用 super().__init__
        self.entity_description = entity_description
        self._attr_translation_key = entity_description.translation_key
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{self._device_id}_{entity_description.key}"
        self.entity_id = f"sensor.petkit_feeder_{self._device_id}_{entity_description.key}"

        _LOGGER.debug(
            "[PetkitFeeder] Sensor initialized: entity_id=%s, unique_id=%s, device_id=%s",
            self.entity_id,
            self._attr_unique_id,
            self._device_id,
        )

    def _get_device(self) -> Feeder | None:
        """获取设备数据."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("device_info")

    @property
    def native_value(self) -> Any:
        """返回传感器值."""
        device = self._get_device()
        if not device or not self.entity_description.value_fn:
            return None
        return self.entity_description.value_fn(device)


# ============ 复杂传感器（保留原有实现） ============


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


class PetkitLastFeedingSensor(PetkitSensorBase):
    """最后喂食时间传感器."""

    _attr_translation_key = "last_feeding"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock-outline"

    @property
    def native_value(self) -> datetime | None:
        """返回最后喂食时间."""
        device = self._get_device()
        if not device:
            return None

        device_records = getattr(device, "device_records", None)
        if not device_records:
            return None

        feed_records = getattr(device_records, "feed", None)
        if not feed_records:
            return None

        latest_completed_at = None

        for record in feed_records:
            items = getattr(record, "items", [])
            for item in items:
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

        try:
            dt = datetime.fromisoformat(latest_completed_at.replace("Z", "+00:00"))
            return dt
        except (ValueError, TypeError):
            return None


class PetkitLastAmountSensor(PetkitSensorBase):
    """最后喂食量传感器."""

    _attr_translation_key = "last_amount"
    _attr_native_unit_of_measurement = "g"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:scale"

    @property
    def native_value(self) -> int | None:
        """返回最后喂食量."""
        device = self._get_device()
        if not device:
            return None

        device_records = getattr(device, "device_records", None)
        if not device_records:
            return None

        feed_records = getattr(device_records, "feed", None)
        if not feed_records:
            return None

        latest_item = None
        latest_completed_at = None

        for record in feed_records:
            items = getattr(record, "items", [])
            for item in items:
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

        state = getattr(latest_item, "state", None)
        if state:
            real_amount = getattr(state, "real_amount", None)
            if real_amount is not None:
                return real_amount

        return getattr(latest_item, "amount", None)


class PetkitTodayCountSensor(PetkitSensorBase):
    """今日喂食次数传感器."""

    _attr_translation_key = "today_count"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:numeric"

    @property
    def native_value(self) -> int | None:
        """返回今日喂食次数."""
        device = self._get_device()
        if not device:
            return None

        if hasattr(device, "today_feeding_count"):
            return device.today_feeding_count

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
        current_weekday = now.weekday() + 1
        current_time = now.strftime("%H:%M")
        current_seconds = now.hour * 3600 + now.minute * 60
        today_date = int(now.strftime("%Y%m%d"))

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
        """返回喂食计划的详细数据."""
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

        return {"schedule": schedule}


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

        return {
            "records": records,
            "week_plan_amount": week_plan_amount,
            "week_real_amount": week_real_amount,
            "week_completed_count": week_completed_count,
            "today_plan_amount": today_plan_amount,
            "today_real_amount": today_real_amount,
            "today_count": today_count,
            "today_completed_count": today_completed_count,
        }