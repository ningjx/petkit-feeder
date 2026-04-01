"""设备型号模块汇总"""

from .base import PetkitDevice, DeviceType, DeviceCapabilities, DeviceEntityConfig
from .d3 import D3Device
from .d4 import D4Device
from .d4s import D4SDevice
from .mini import MiniDevice
from .factory import DeviceFactory

__all__ = [
    "PetkitDevice",
    "DeviceType",
    "DeviceCapabilities",
    "DeviceEntityConfig",
    "D3Device",
    "D4Device",
    "D4SDevice",
    "MiniDevice",
    "DeviceFactory",
]