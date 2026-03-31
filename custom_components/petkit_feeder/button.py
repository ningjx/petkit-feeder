"""按钮实体 - 刷新按钮、手动出粮按钮."""

from __future__ import annotations

import logging
from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, BUTTON_REFRESH, DEFAULT_NAME
from .coordinator import PetkitDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置按钮实体."""
    coordinator: PetkitDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = [
        PetkitRefreshButton(coordinator, config_entry),
        PetkitManualFeedButton(coordinator, config_entry),
    ]
    
    async_add_entities(entities)


class PetkitRefreshButton(CoordinatorEntity, ButtonEntity):
    """小佩 SOLO 刷新按钮."""

    _attr_has_entity_name = True
    _attr_translation_key = "refresh"

    def __init__(
        self,
        coordinator: PetkitDataUpdateCoordinator,
        config_entry,
    ) -> None:
        """初始化刷新按钮."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_{BUTTON_REFRESH}"
        self._attr_name = "刷新数据"
        self._attr_icon = "mdi:refresh"

    async def async_press(self) -> None:
        """按下按钮时刷新数据."""
        await self.coordinator.async_request_refresh()

    @property
    def device_info(self):
        """返回设备信息."""
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": DEFAULT_NAME,
            "manufacturer": "Petkit",
            "model": "SOLO",
        }


class PetkitManualFeedButton(CoordinatorEntity, ButtonEntity):
    """手动出粮按钮."""

    _attr_has_entity_name = True
    _attr_translation_key = "manual_feed"

    def __init__(
        self,
        coordinator: PetkitDataUpdateCoordinator,
        config_entry,
    ) -> None:
        """初始化手动出粮按钮."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_manual_feed"
        self._attr_name = "手动出粮"
        self._attr_icon = "mdi:food-drumstick"

    async def async_press(self) -> None:
        """按下按钮时手动出粮."""
        _LOGGER.info("触发手动出粮")
        await self.coordinator.manual_feed()

    @property
    def device_info(self):
        """返回设备信息."""
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": DEFAULT_NAME,
            "manufacturer": "Petkit",
            "model": "SOLO",
        }
