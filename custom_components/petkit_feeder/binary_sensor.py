"""二进制传感器实体."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.binary_sensor import BinarySensorEntityDescription, BinarySensorDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, LOW_FOOD_THRESHOLD
from .coordinator import PetkitDataUpdateCoordinator
from .entities import PetkitBinarySensorEntity
from .pypetkitapi.feeder_container import Feeder

_LOGGER = logging.getLogger(__name__)


@dataclass(kw_only=True)
class PetkitBinarySensorEntityDescription(BinarySensorEntityDescription):
    """描述 Petkit 二进制传感器实体."""

    value_fn: Callable[[Feeder], bool | None] | None = None


BINARY_SENSORS: tuple[PetkitBinarySensorEntityDescription, ...] = (
    PetkitBinarySensorEntityDescription(
        key="online",
        translation_key="online",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        icon="mdi:wifi",
        value_fn=lambda device: (
            getattr(device, "is_online", None)
            or (getattr(getattr(device, "state", None), "overall", None) == 1)
            or (getattr(getattr(device, "state", None), "wifi", None) is not None)
        ),
    ),
    PetkitBinarySensorEntityDescription(
        key="low_food",
        translation_key="low_food",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:alert-circle",
        value_fn=lambda device: _get_low_food_status(device),
    ),
    PetkitBinarySensorEntityDescription(
        key="battery_status",
        translation_key="battery_status",
        device_class=BinarySensorDeviceClass.POWER,
        icon="mdi:battery",
        value_fn=lambda device: (
            getattr(getattr(device, "state", None), "battery_status", None) == 1
            if getattr(getattr(device, "state", None), "battery_status", None) is not None
            else None
        ),
    ),
    PetkitBinarySensorEntityDescription(
        key="battery_power",
        translation_key="battery_power",
        device_class=BinarySensorDeviceClass.POWER,
        icon="mdi:battery",
        value_fn=lambda device: (
            getattr(getattr(device, "state", None), "battery_power", None) == 1
            if getattr(getattr(device, "state", None), "battery_power", None) is not None
            else None
        ),
    ),
)


def _get_low_food_status(device: Feeder) -> bool | None:
    """获取缺粮状态."""
    food_level = None
    if hasattr(device, "desiccant_left_percent"):
        food_level = device.desiccant_left_percent
    elif hasattr(device, "food_level"):
        food_level = device.food_level

    if food_level is None:
        state = getattr(device, "state", None)
        food_flag = getattr(state, "food", None) if state is not None else None
        if food_flag is None:
            return None
        return food_flag == 0

    return food_level < LOW_FOOD_THRESHOLD


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置二进制传感器实体."""
    coordinator: PetkitDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []

    # 添加所有二进制传感器
    for description in BINARY_SENSORS:
        entities.append(PetkitBinarySensor(coordinator, config_entry, description))

    async_add_entities(entities)


class PetkitBinarySensor(PetkitBinarySensorEntity):
    """二进制传感器实体."""

    entity_description: PetkitBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: PetkitDataUpdateCoordinator,
        config_entry,
        entity_description: PetkitBinarySensorEntityDescription,
    ) -> None:
        """初始化二进制传感器."""
        # 先设置 entity_description 和 translation_key，再调用 super().__init__
        self.entity_description = entity_description
        self._attr_translation_key = entity_description.translation_key
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{self._device_id}_{entity_description.key}"
        self.entity_id = f"binary_sensor.petkit_feeder_{self._device_id}_{entity_description.key}"

        _LOGGER.debug(
            "[PetkitFeeder] BinarySensor initialized: entity_id=%s, unique_id=%s, device_id=%s",
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
    def is_on(self) -> bool | None:
        """返回传感器状态."""
        device = self._get_device()
        if not device or not self.entity_description.value_fn:
            return None
        return self.entity_description.value_fn(device)