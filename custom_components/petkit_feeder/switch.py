"""开关实体 - 设备设置开关."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from homeassistant.components.switch import SwitchEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import PetkitDataUpdateCoordinator
from .entities import PetkitSwitchEntity

_LOGGER = logging.getLogger(__name__)


@dataclass(kw_only=True)
class PetkitSwitchEntityDescription(SwitchEntityDescription):
    """描述 Petkit 开关实体."""

    setting_key: str  # API 调用时的键名
    settings_attr: str  # settings 对象中的属性名


SWITCHES: tuple[PetkitSwitchEntityDescription, ...] = (
    PetkitSwitchEntityDescription(
        key="light_mode",
        translation_key="light_mode",
        icon="mdi:lightbulb",
        setting_key="lightMode",
        settings_attr="light_mode",
    ),
    PetkitSwitchEntityDescription(
        key="food_warn",
        translation_key="food_warn",
        icon="mdi:alert",
        setting_key="foodWarn",
        settings_attr="food_warn",
    ),
    PetkitSwitchEntityDescription(
        key="feed_notify",
        translation_key="feed_notify",
        icon="mdi:bell",
        setting_key="feedNotify",
        settings_attr="feed_notify",
    ),
    PetkitSwitchEntityDescription(
        key="manual_lock",
        translation_key="manual_lock",
        icon="mdi:lock",
        setting_key="manualLock",
        settings_attr="manual_lock",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置开关实体."""
    coordinator: PetkitDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = [
        PetkitSwitch(coordinator, config_entry, description)
        for description in SWITCHES
    ]

    async_add_entities(entities)


class PetkitSwitch(PetkitSwitchEntity):
    """Petkit 开关实体."""

    entity_description: PetkitSwitchEntityDescription

    def __init__(
        self,
        coordinator: PetkitDataUpdateCoordinator,
        config_entry,
        entity_description: PetkitSwitchEntityDescription,
    ) -> None:
        """初始化开关."""
        self.entity_description = entity_description
        self._attr_translation_key = entity_description.translation_key
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{self._device_id}_{entity_description.key}"
        self.entity_id = f"switch.petkit_feeder_{self._device_id}_{entity_description.key}"

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
        return getattr(settings, self.entity_description.settings_attr, 0) == 1

    async def async_turn_on(self, **kwargs) -> None:
        """打开开关."""
        await self._update_setting(self.entity_description.setting_key, 1)

    async def async_turn_off(self, **kwargs) -> None:
        """关闭开关."""
        await self._update_setting(self.entity_description.setting_key, 0)

    async def _update_setting(self, key: str, value: int) -> bool:
        """更新设备设置."""
        return await self.coordinator.update_setting(key, value)