"""PetKit 喂食器 Home Assistant 集成."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import PetkitDataUpdateCoordinator
from .services import FeedingService, SERVICE_SCHEMAS

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """设置集成入口."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = PetkitDataUpdateCoordinator(
        hass,
        username=entry.data["username"],
        password=entry.data["password"],
        device_id=entry.data["device_id"],
        region=entry.data.get("region", "CN"),
        refresh_mode=entry.options.get("refresh_mode", "auto"),
        refresh_interval=entry.options.get("refresh_interval", 300),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_update_options))

    # 只在第一个配置条目时注册服务
    if len(hass.data[DOMAIN]) == 1:
        feeding_service = FeedingService(hass)
        feeding_service.register_services(SERVICE_SCHEMAS)
        _LOGGER.info("已注册所有喂食服务")

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """卸载集成."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.cleanup()

        # 所有配置条目都卸载后，注销服务
        if not hass.data[DOMAIN]:
            feeding_service = FeedingService(hass)
            feeding_service.unregister_services(list(SERVICE_SCHEMAS.keys()))
            _LOGGER.info("已注销所有喂食服务")

    return unload_ok


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """更新选项时重新加载."""
    await hass.config_entries.async_reload(entry.entry_id)