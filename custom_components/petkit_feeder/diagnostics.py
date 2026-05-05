"""诊断支持 - 导出调试信息."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import PetkitDataUpdateCoordinator

TO_REDACT = {
    "password",
    "username",
    "token",
    "api_key",
    "_password",
    "_username",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """返回配置条目的诊断信息."""
    coordinator: PetkitDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    data: dict[str, Any] = {
        "entry": async_redact_data(entry.as_dict(), TO_REDACT),
        "coordinator_data": _get_coordinator_data(coordinator),
        "device_info": _get_device_info(coordinator),
    }

    return async_redact_data(data, TO_REDACT)


def _get_coordinator_data(coordinator: PetkitDataUpdateCoordinator) -> dict[str, Any]:
    """提取协调器数据."""
    if not coordinator.data:
        return {"error": "No data available"}

    device_info = coordinator.data.get("device_info")
    if not device_info:
        return {"error": "No device info"}

    # 提取关键状态信息（不含敏感数据）
    state_data = {}
    if hasattr(device_info, "state") and device_info.state:
        state = device_info.state
        state_data = {
            "overall": getattr(state, "overall", None),
            "food_state": getattr(state, "food_state", None),
            "desiccant_state": getattr(state, "desiccant_state", None),
            "battery_power": getattr(state, "battery_power", None),
            "battery_status": getattr(state, "battery_status", None),
        }

    return {
        "device_id": coordinator.data.get("device_id"),
        "state": state_data,
    }


def _get_device_info(coordinator: PetkitDataUpdateCoordinator) -> dict[str, Any]:
    """提取设备信息."""
    device_info = coordinator.data.get("device_info") if coordinator.data else None

    if not device_info:
        return {"error": "No device info available"}

    # 提取设备基本信息（不含敏感数据）
    info: dict[str, Any] = {
        "name": getattr(device_info, "name", None),
        "device_id": getattr(device_info, "id", None),
    }

    # 提取设备型号信息
    if hasattr(device_info, "device_nfo") and device_info.device_nfo:
        info["model"] = getattr(device_info.device_nfo, "modele_name", None)
        info["device_type"] = getattr(device_info.device_nfo, "device_type", None)

    # 提取 WiFi 信息（不含 SSID）
    if hasattr(device_info, "state") and device_info.state:
        wifi = getattr(device_info.state, "wifi", None)
        if wifi:
            info["wifi_signal"] = getattr(wifi, "rsq", None)

    return info