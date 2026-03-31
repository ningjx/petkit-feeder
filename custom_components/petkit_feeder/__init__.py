"""PetKit 喂食器 Home Assistant 集成."""

from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN
from .coordinator import PetkitDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SWITCH,
]

ADD_FEEDING_ITEM_SCHEMA = vol.Schema({
    vol.Optional("entry_id"): cv.string,
    vol.Required("day"): vol.All(vol.Coerce(int), vol.Range(min=1, max=7)),
    vol.Required("time"): cv.string,
    vol.Required("amount"): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
    vol.Optional("name", default=""): cv.string,
})

REMOVE_FEEDING_ITEM_SCHEMA = vol.Schema({
    vol.Optional("entry_id"): cv.string,
    vol.Required("day"): vol.All(vol.Coerce(int), vol.Range(min=1, max=7)),
    vol.Required("item_id"): cv.string,
})

TOGGLE_FEEDING_ITEM_SCHEMA = vol.Schema({
    vol.Optional("entry_id"): cv.string,
    vol.Required("day"): vol.All(vol.Coerce(int), vol.Range(min=1, max=7)),
    vol.Required("item_id"): cv.string,
    vol.Required("enabled"): cv.boolean,
})

UPDATE_FEEDING_ITEM_SCHEMA = vol.Schema({
    vol.Optional("entry_id"): cv.string,
    vol.Required("day"): vol.All(vol.Coerce(int), vol.Range(min=1, max=7)),
    vol.Required("item_id"): cv.string,
    vol.Optional("time"): cv.string,
    vol.Optional("amount"): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
    vol.Optional("name"): cv.string,
})


def _get_coordinator(hass: HomeAssistant, entry_id: str | None) -> PetkitDataUpdateCoordinator:
    """获取协调器实例."""
    if entry_id:
        return hass.data[DOMAIN][entry_id]
    for coord in hass.data[DOMAIN].values():
        return coord
    raise ValueError("未找到任何 PetKit 喂食器配置")


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

    if len(hass.data[DOMAIN]) == 1:
        hass.services.async_register(
            DOMAIN,
            "add_feeding_item",
            _handle_add_feeding_item_wrapper(hass),
            schema=ADD_FEEDING_ITEM_SCHEMA,
        )
        hass.services.async_register(
            DOMAIN,
            "remove_feeding_item",
            _handle_remove_feeding_item_wrapper(hass),
            schema=REMOVE_FEEDING_ITEM_SCHEMA,
        )
        hass.services.async_register(
            DOMAIN,
            "toggle_feeding_item",
            _handle_toggle_feeding_item_wrapper(hass),
            schema=TOGGLE_FEEDING_ITEM_SCHEMA,
        )
        hass.services.async_register(
            DOMAIN,
            "update_feeding_item",
            _handle_update_feeding_item_wrapper(hass),
            schema=UPDATE_FEEDING_ITEM_SCHEMA,
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """卸载集成."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.cleanup()

        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, "add_feeding_item")
            hass.services.async_remove(DOMAIN, "remove_feeding_item")
            hass.services.async_remove(DOMAIN, "toggle_feeding_item")
            hass.services.async_remove(DOMAIN, "update_feeding_item")

    return unload_ok


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """更新选项时重新加载."""
    await hass.config_entries.async_reload(entry.entry_id)


async def _handle_add_feeding_item(hass: HomeAssistant, call: ServiceCall) -> None:
    """处理新增喂食计划服务调用."""
    coordinator = _get_coordinator(hass, call.data.get("entry_id"))
    day = call.data["day"]
    time_str = call.data["time"]
    amount = call.data["amount"]
    name = call.data.get("name", "")
    
    _LOGGER.info("新增喂食计划: 周%d %s %dg %s", day, time_str, amount, name)
    await coordinator.add_feeding_item(day, time_str, amount, name)


def _handle_add_feeding_item_wrapper(hass: HomeAssistant):
    """返回异步服务处理函数."""
    async def handler(call: ServiceCall) -> None:
        await _handle_add_feeding_item(hass, call)
    return handler


async def _handle_remove_feeding_item(hass: HomeAssistant, call: ServiceCall) -> None:
    """处理删除喂食计划服务调用."""
    coordinator = _get_coordinator(hass, call.data.get("entry_id"))
    day = call.data["day"]
    item_id = call.data["item_id"]
    
    _LOGGER.info("删除喂食计划: 周%d %s", day, item_id)
    await coordinator.remove_feeding_item(day, item_id)


def _handle_remove_feeding_item_wrapper(hass: HomeAssistant):
    """返回异步服务处理函数."""
    async def handler(call: ServiceCall) -> None:
        await _handle_remove_feeding_item(hass, call)
    return handler


async def _handle_toggle_feeding_item(hass: HomeAssistant, call: ServiceCall) -> None:
    """处理启用/禁用喂食计划服务调用."""
    coordinator = _get_coordinator(hass, call.data.get("entry_id"))
    day = call.data["day"]
    item_id = call.data["item_id"]
    enabled = call.data["enabled"]
    
    _LOGGER.info("切换喂食计划状态: 周%d %s %s", day, item_id, "启用" if enabled else "禁用")
    await coordinator.toggle_feeding_item(day, item_id, enabled)


def _handle_toggle_feeding_item_wrapper(hass: HomeAssistant):
    """返回异步服务处理函数."""
    async def handler(call: ServiceCall) -> None:
        await _handle_toggle_feeding_item(hass, call)
    return handler


async def _handle_update_feeding_item(hass: HomeAssistant, call: ServiceCall) -> None:
    """处理更新喂食计划服务调用."""
    coordinator = _get_coordinator(hass, call.data.get("entry_id"))
    day = call.data["day"]
    item_id = call.data["item_id"]
    time_str = call.data.get("time")
    amount = call.data.get("amount")
    name = call.data.get("name")
    
    _LOGGER.info("更新喂食计划: 周%d %s", day, item_id)
    await coordinator.update_feeding_item(day, item_id, time_str, amount, name)


def _handle_update_feeding_item_wrapper(hass: HomeAssistant):
    """返回异步服务处理函数."""
    async def handler(call: ServiceCall) -> None:
        await _handle_update_feeding_item(hass, call)
    return handler