"""二进制传感器实体."""

from __future__ import annotations

import logging
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .pypetkitapi.feeder_container import Feeder

from .const import DOMAIN, DEFAULT_NAME, LOW_FOOD_THRESHOLD
from .coordinator import PetkitDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置二进制传感器实体."""
    coordinator: PetkitDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = [
        PetkitOnlineSensor(coordinator, config_entry),
        PetkitLowFoodSensor(coordinator, config_entry),
    ]
    
    # 添加电池相关传感器（如果设备支持）
    device = coordinator.data.get("device_info") if coordinator.data else None
    if device and hasattr(device, "state") and device.state:
        # 电池状态（有/没有电池）
        if hasattr(device.state, "battery_status") and device.state.battery_status is not None:
            entities.append(PetkitBatteryStatusSensor(coordinator, config_entry))
        
        # 电池供电（是否使用电池供电）
        if hasattr(device.state, "battery_power") and device.state.battery_power is not None:
            entities.append(PetkitBatteryPowerSensor(coordinator, config_entry))
    
    async_add_entities(entities)


class PetkitBinarySensorBase(CoordinatorEntity, BinarySensorEntity):
    """小佩二进制传感器基类."""

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


class PetkitOnlineSensor(PetkitBinarySensorBase):
    """在线状态传感器."""

    _attr_translation_key = "online"
    _attr_device_class = "connectivity"
    _attr_icon = "mdi:wifi"

    @property
    def is_on(self) -> bool | None:
        """返回在线状态."""
        device = self._get_device()
        if not device:
            return None

        # 优先使用库自带的在线标志（如果未来提供）
        if hasattr(device, "is_online"):
            return device.is_online

        # 当前版本可以根据状态里的 overall / wifi 判断在线
        state = getattr(device, "state", None)
        overall = getattr(state, "overall", None) if state is not None else None

        if overall is not None:
            # overall==1 代表设备工作正常
            return overall == 1

        wifi = getattr(state, "wifi", None) if state is not None else None
        if wifi is not None:
            # 有 WiFi 信息，一般认为在线
            return True

        return None


class PetkitLowFoodSensor(PetkitBinarySensorBase):
    """缺粮警告传感器."""

    _attr_translation_key = "low_food"
    _attr_device_class = "problem"
    _attr_icon = "mdi:alert-circle"

    @property
    def is_on(self) -> bool | None:
        """返回缺粮状态."""
        device = self._get_device()
        if not device:
            return None

        # 从 pypetkitapi 的 Feeder 对象获取粮量
        food_level = None
        if hasattr(device, "desiccant_left_percent"):
            food_level = device.desiccant_left_percent
        elif hasattr(device, "food_level"):
            food_level = device.food_level

        # 如果没有百分比，退化为根据状态里的 food 标志判断：0=无粮，1=有粮
        if food_level is None:
            state = getattr(device, "state", None)
            food_flag = getattr(state, "food", None) if state is not None else None
            if food_flag is None:
                return None
            # food_flag == 0 认为“缺粮”
            return food_flag == 0

        return food_level < LOW_FOOD_THRESHOLD


# ============ 新增：电池状态传感器 ============

class PetkitBatteryStatusSensor(PetkitBinarySensorBase):
    """电池状态传感器（有/没有电池）."""

    _attr_translation_key = "battery_status"
    _attr_icon = "mdi:battery"
    _attr_device_class = "power"

    @property
    def is_on(self) -> bool | None:
        """返回电池状态（True=有电池，False=没有电池）."""
        device = self._get_device()
        if not device:
            return None
        state = getattr(device, "state", None)
        if not state:
            return None
        battery_status = getattr(state, "battery_status", None)
        # battery_status=1 表示有电池，0 表示没有
        return battery_status == 1 if battery_status is not None else None


class PetkitBatteryPowerSensor(PetkitBinarySensorBase):
    """电池供电传感器（是否使用电池供电）."""

    _attr_translation_key = "battery_power"
    _attr_icon = "mdi:battery"
    _attr_device_class = "power"

    @property
    def is_on(self) -> bool | None:
        """返回电池供电状态（True=电池供电，False=电源供电）."""
        device = self._get_device()
        if not device:
            return None
        state = getattr(device, "state", None)
        if not state:
            return None
        battery_power = getattr(state, "battery_power", None)
        # battery_power=1 表示电池供电，0 表示电源供电
        return battery_power == 1 if battery_power is not None else None
