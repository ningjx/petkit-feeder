"""D3 设备实现（占位）"""

from __future__ import annotations

from typing import Any

from .base import PetkitDevice, DeviceType, DeviceCapabilities, DeviceEntityConfig


class D3Device(PetkitDevice):
    """D3 喂食器设备（待实现）."""
    
    @property
    def device_type(self) -> DeviceType:
        """设备类型."""
        return DeviceType.D3
    
    @property
    def model_name(self) -> str:
        """设备型号名称."""
        return "PetKit D3"
    
    @property
    def capabilities(self) -> DeviceCapabilities:
        """设备能力配置."""
        return DeviceCapabilities(
            supports_schedule=True,
            supports_manual_feed=True,
            supports_feeding_history=True,
            supports_food_level=True,
        )
    
    @property
    def entity_config(self) -> DeviceEntityConfig:
        """设备实体配置."""
        return DeviceEntityConfig()