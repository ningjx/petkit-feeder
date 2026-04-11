"""按钮实体 - 刷新按钮、手动出粮按钮."""

from __future__ import annotations

import logging
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, BUTTON_REFRESH
from .coordinator import PetkitDataUpdateCoordinator
from .entities import PetkitButtonEntity

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


class PetkitRefreshButton(PetkitButtonEntity):
    """小佩喂食器刷新按钮."""

    _attr_translation_key = "refresh"

    def __init__(
        self,
        coordinator: PetkitDataUpdateCoordinator,
        config_entry,
    ) -> None:
        """初始化刷新按钮."""
        super().__init__(coordinator, config_entry, BUTTON_REFRESH)
        self._attr_icon = "mdi:refresh"
        
        _LOGGER.debug(
            "[PetkitFeeder] Button initialized: entity_id=%s, unique_id=%s, device_id=%s",
            self.entity_id,
            self._attr_unique_id,
            self._device_id,
        )

    async def async_press(self) -> None:
        """按下按钮时刷新数据."""
        await self.coordinator.async_request_refresh()


class PetkitManualFeedButton(PetkitButtonEntity):
    """手动出粮按钮."""

    _attr_translation_key = "manual_feed"

    def __init__(
        self,
        coordinator: PetkitDataUpdateCoordinator,
        config_entry,
    ) -> None:
        """初始化手动出粮按钮."""
        super().__init__(coordinator, config_entry)
        self._attr_icon = "mdi:food-drumstick"
        
        _LOGGER.debug(
            "[PetkitFeeder] Button initialized: entity_id=%s, unique_id=%s, device_id=%s",
            self.entity_id,
            self._attr_unique_id,
            self._device_id,
        )

    async def async_press(self) -> None:
        """按下按钮时手动出粮."""
        _LOGGER.info("触发手动出粮")
        await self.coordinator.manual_feed()
