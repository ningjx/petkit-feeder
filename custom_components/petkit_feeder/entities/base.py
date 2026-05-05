"""PetKit 实体基类"""

from __future__ import annotations

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import DOMAIN, DEFAULT_NAME
from ..coordinator import PetkitDataUpdateCoordinator


class PetkitEntity(CoordinatorEntity):
    """PetKit 实体基类."""

    def __init__(
        self,
        coordinator: PetkitDataUpdateCoordinator,
        config_entry,
    ) -> None:
        """初始化实体基类."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._device_id = getattr(coordinator, "_device_id", "unknown")

    @property
    def device_info(self) -> dict:
        """返回设备信息."""
        device = self._get_device()
        model = "Unknown"
        device_name = DEFAULT_NAME
        firmware_version = None

        if device:
            # 获取设备型号
            if hasattr(device, "device_nfo") and device.device_nfo:
                model = device.device_nfo.modele_name or "Unknown"
            # 获取设备名称
            if hasattr(device, "name") and device.name:
                device_name = device.name
            # 获取固件版本
            if hasattr(device, "firmware"):
                firmware_version = str(device.firmware)

        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": device_name,
            "manufacturer": "Petkit",
            "model": model,
            "sw_version": firmware_version
        }

    def _get_device(self):
        """获取设备数据."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("device_info")

    def _get_settings(self):
        """获取设备设置."""
        device = self._get_device()
        if not device:
            return None
        return getattr(device, "settings", None)

    def _get_state(self):
        """获取设备状态."""
        device = self._get_device()
        if not device:
            return None
        return getattr(device, "state", None)