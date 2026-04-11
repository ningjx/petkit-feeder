"""开关实体 - 设备设置开关."""

from __future__ import annotations

import logging
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import PetkitDataUpdateCoordinator
from .entities import PetkitSwitchEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置开关实体."""
    coordinator: PetkitDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = [
        PetkitLightModeSwitch(coordinator, config_entry),
        PetkitFoodWarnSwitch(coordinator, config_entry),
        PetkitFeedNotifySwitch(coordinator, config_entry),
        PetkitManualLockSwitch(coordinator, config_entry),
    ]
    
    async_add_entities(entities)


class PetkitSwitchBase(PetkitSwitchEntity):
    """开关基类."""

    async def _update_setting(self, key: str, value: int) -> bool:
        """更新设备设置."""
        return await self.coordinator.update_setting(key, value)


class PetkitLightModeSwitch(PetkitSwitchBase):
    """指示灯模式开关."""

    _attr_translation_key = "light_mode"
    _attr_icon = "mdi:lightbulb"

    def __init__(self, coordinator, config_entry) -> None:
        """初始化."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{self._device_id}_light_mode"
        self.entity_id = f"switch.petkit_feeder_{self._device_id}_light_mode"
        
        _LOGGER.debug(
            "[PetkitFeeder] Switch initialized: entity_id=%s, unique_id=%s, device_id=%s",
            self.entity_id,
            self._attr_unique_id,
            self._device_id,
        )

    @property
    def is_on(self) -> bool | None:
        """返回开关状态."""
        settings = self._get_settings()
        if not settings:
            return None
        return getattr(settings, "light_mode", 0) == 1

    async def async_turn_on(self, **kwargs) -> None:
        """打开开关."""
        await self._update_setting("lightMode", 1)

    async def async_turn_off(self, **kwargs) -> None:
        """关闭开关."""
        await self._update_setting("lightMode", 0)


class PetkitFoodWarnSwitch(PetkitSwitchBase):
    """缺粮提醒开关."""

    _attr_translation_key = "food_warn"
    _attr_icon = "mdi:alert"

    def __init__(self, coordinator, config_entry) -> None:
        """初始化."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{self._device_id}_food_warn"
        self.entity_id = f"switch.petkit_feeder_{self._device_id}_food_warn"
        
        _LOGGER.debug(
            "[PetkitFeeder] Switch initialized: entity_id=%s, unique_id=%s, device_id=%s",
            self.entity_id,
            self._attr_unique_id,
            self._device_id,
        )

    @property
    def is_on(self) -> bool | None:
        """返回开关状态."""
        settings = self._get_settings()
        if not settings:
            return None
        return getattr(settings, "food_warn", 0) == 1

    async def async_turn_on(self, **kwargs) -> None:
        """打开开关."""
        await self._update_setting("foodWarn", 1)

    async def async_turn_off(self, **kwargs) -> None:
        """关闭开关."""
        await self._update_setting("foodWarn", 0)


class PetkitFeedNotifySwitch(PetkitSwitchBase):
    """喂食通知开关."""

    _attr_translation_key = "feed_notify"
    _attr_icon = "mdi:bell"

    def __init__(self, coordinator, config_entry) -> None:
        """初始化."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{self._device_id}_feed_notify"
        self.entity_id = f"switch.petkit_feeder_{self._device_id}_feed_notify"
        
        _LOGGER.debug(
            "[PetkitFeeder] Switch initialized: entity_id=%s, unique_id=%s, device_id=%s",
            self.entity_id,
            self._attr_unique_id,
            self._device_id,
        )

    @property
    def is_on(self) -> bool | None:
        """返回开关状态."""
        settings = self._get_settings()
        if not settings:
            return None
        return getattr(settings, "feed_notify", 0) == 1

    async def async_turn_on(self, **kwargs) -> None:
        """打开开关."""
        await self._update_setting("feedNotify", 1)

    async def async_turn_off(self, **kwargs) -> None:
        """关闭开关."""
        await self._update_setting("feedNotify", 0)


class PetkitManualLockSwitch(PetkitSwitchBase):
    """手动锁定开关."""

    _attr_translation_key = "manual_lock"
    _attr_icon = "mdi:lock"

    def __init__(self, coordinator, config_entry) -> None:
        """初始化."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{self._device_id}_manual_lock"
        self.entity_id = f"switch.petkit_feeder_{self._device_id}_manual_lock"
        
        _LOGGER.debug(
            "[PetkitFeeder] Switch initialized: entity_id=%s, unique_id=%s, device_id=%s",
            self.entity_id,
            self._attr_unique_id,
            self._device_id,
        )

    @property
    def is_on(self) -> bool | None:
        """返回开关状态."""
        settings = self._get_settings()
        if not settings:
            return None
        return getattr(settings, "manual_lock", 0) == 1

    async def async_turn_on(self, **kwargs) -> None:
        """打开开关."""
        await self._update_setting("manualLock", 1)

    async def async_turn_off(self, **kwargs) -> None:
        """关闭开关."""
        await self._update_setting("manualLock", 0)