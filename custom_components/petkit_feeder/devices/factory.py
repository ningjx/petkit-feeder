"""设备工厂 - 根据设备类型创建设备实例"""

from __future__ import annotations

import logging
from typing import Any

from .base import PetkitDevice, DeviceType
from .d3 import D3Device
from .d4 import D4Device
from .d4s import D4SDevice
from .mini import MiniDevice

_LOGGER = logging.getLogger(__name__)


class DeviceFactory:
    """设备工厂.
    
    根据设备类型字符串创建对应的设备实例。
    """
    
    # 设备类型映射
    _device_classes = {
        DeviceType.D4: D4Device,
        DeviceType.D3: D3Device,
        DeviceType.D4S: D4SDevice,
        DeviceType.FEEDER_MINI: MiniDevice,
    }
    
    # 设备类型字符串映射
    _type_string_map = {
        "d4": DeviceType.D4,
        "d3": DeviceType.D3,
        "d4s": DeviceType.D4S,
        "feeder_mini": DeviceType.FEEDER_MINI,
        "solo": DeviceType.D4,  # Fresh Element Solo = D4
        "fresh element solo": DeviceType.D4,
    }
    
    @classmethod
    def create(cls, device_data: Any) -> PetkitDevice:
        """创建设备实例.
        
        Args:
            device_data: API 返回的设备数据
            
        Returns:
            设备实例
            
        Raises:
            ValueError: 不支持的设备类型
        """
        device_type = cls._detect_device_type(device_data)
        
        if device_type is None:
            raise ValueError(f"无法识别的设备类型: {device_data}")
        
        device_class = cls._device_classes.get(device_type)
        
        if device_class is None:
            raise ValueError(f"设备类型 {device_type.value} 尚未实现")
        
        _LOGGER.info(
            "创建设备实例: %s (%s)",
            device_class.__name__,
            device_data.name if hasattr(device_data, 'name') else 'Unknown'
        )
        
        return device_class(device_data)
    
    @classmethod
    def _detect_device_type(cls, device_data: Any) -> DeviceType | None:
        """检测设备类型.
        
        Args:
            device_data: 设备数据
            
        Returns:
            设备类型枚举值
        """
        # 优先使用 device_type 字段
        if hasattr(device_data, 'device_type'):
            device_type_str = device_data.device_type.lower()
            if device_type_str in cls._type_string_map:
                return cls._type_string_map[device_type_str]
        
        # 其次使用 modele_name 字段
        if hasattr(device_data, 'device_nfo') and device_data.device_nfo:
            modele_name = getattr(device_data.device_nfo, 'modele_name', '')
            if modele_name:
                modele_lower = modele_name.lower()
                for key, device_type in cls._type_string_map.items():
                    if key in modele_lower:
                        return device_type
        
        # 默认返回 D4
        return DeviceType.D4
    
    @classmethod
    def is_supported(cls, device_data: Any) -> bool:
        """检查设备是否受支持.
        
        Args:
            device_data: 设备数据
            
        Returns:
            是否受支持
        """
        try:
            device_type = cls._detect_device_type(device_data)
            return device_type is not None and cls._device_classes.get(device_type) is not None
        except Exception:
            return False
    
    @classmethod
    def get_supported_models(cls) -> list[str]:
        """获取支持的设备型号列表.
        
        Returns:
            支持的型号名称列表
        """
        supported = []
        for device_type, device_class in cls._device_classes.items():
            if device_class is not None:
                supported.append(f"{device_type.value} ({device_class(None).model_name})")
        return supported