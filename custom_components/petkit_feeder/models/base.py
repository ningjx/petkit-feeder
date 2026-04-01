"""设备基类定义"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DeviceType(Enum):
    """设备类型枚举."""
    D3 = "d3"
    D4 = "d4"
    D4S = "d4s"
    FEEDER_MINI = "feeder_mini"


@dataclass
class DeviceCapabilities:
    """设备能力配置."""
    
    # 基础能力
    supports_schedule: bool = True
    supports_manual_feed: bool = True
    supports_feeding_history: bool = True
    supports_food_level: bool = True
    
    # 高级能力
    supports_camera: bool = False
    supports_desiccant: bool = True
    supports_voice: bool = False
    supports_calibration: bool = True
    supports_wifi_info: bool = True
    
    # 传感器配置
    supports_real_amount_total: bool = True
    supports_plan_amount_total: bool = True
    supports_add_amount_total: bool = True
    supports_plan_real_amount_total: bool = True


@dataclass
class DeviceEntityConfig:
    """设备实体配置.
    
    定义该设备支持哪些传感器、开关、按钮等。
    """
    
    # 传感器列表
    sensors: list[str] = field(default_factory=lambda: [
        "device_name",
        "device_id",
        "last_feeding",
        "last_amount",
        "today_count",
        "feeding_schedule",
        "feeding_history",
    ])
    
    # 统计传感器（需要设备支持）
    stat_sensors: list[str] = field(default_factory=lambda: [
        "real_amount_total",
        "plan_amount_total",
        "add_amount_total",
        "plan_real_amount_total",
    ])
    
    # WiFi 传感器
    wifi_sensors: list[str] = field(default_factory=lambda: [
        "wifi_ssid",
        "wifi_rsq",
    ])
    
    # 二进制传感器
    binary_sensors: list[str] = field(default_factory=lambda: [
        "online",
    ])
    
    # 按钮
    buttons: list[str] = field(default_factory=lambda: [
        "refresh",
        "manual_feed",
    ])
    
    # 开关
    switches: list[str] = field(default_factory=lambda: [
        "light_mode",
        "food_warn",
        "feed_notify",
        "manual_lock",
    ])
    
    # 数字输入
    numbers: list[str] = field(default_factory=lambda: [
        "feed_amount",
    ])


class PetkitDevice(ABC):
    """PetKit 设备基类.
    
    所有设备型号都需要继承此类，实现自己的配置和逻辑。
    """
    
    def __init__(self, device_data: Any):
        """初始化设备.
        
        Args:
            device_data: API 返回的设备数据
        """
        self._device_data = device_data
    
    @property
    @abstractmethod
    def device_type(self) -> DeviceType:
        """设备类型."""
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """设备型号名称（如 Fresh Element Solo）."""
        pass
    
    @property
    @abstractmethod
    def capabilities(self) -> DeviceCapabilities:
        """设备能力配置."""
        pass
    
    @property
    @abstractmethod
    def entity_config(self) -> DeviceEntityConfig:
        """设备实体配置."""
        pass
    
    @property
    def device_data(self) -> Any:
        """获取设备原始数据."""
        return self._device_data
    
    def get_supported_sensors(self) -> list[str]:
        """获取支持的传感器列表."""
        config = self.entity_config
        sensors = list(config.sensors)
        
        # 根据能力添加统计传感器
        if self.capabilities.supports_real_amount_total:
            sensors.extend(config.stat_sensors)
        
        # 根据能力添加 WiFi 传感器
        if self.capabilities.supports_wifi_info:
            sensors.extend(config.wifi_sensors)
        
        return sensors
    
    def get_supported_binary_sensors(self) -> list[str]:
        """获取支持的二进制传感器列表."""
        return self.entity_config.binary_sensors
    
    def get_supported_buttons(self) -> list[str]:
        """获取支持的按钮列表."""
        buttons = list(self.entity_config.buttons)
        
        # 根据能力添加手动喂食按钮
        if not self.capabilities.supports_manual_feed and "manual_feed" in buttons:
            buttons.remove("manual_feed")
        
        return buttons
    
    def get_supported_switches(self) -> list[str]:
        """获取支持的开关列表."""
        return self.entity_config.switches
    
    def get_supported_numbers(self) -> list[str]:
        """获取支持的数字输入列表."""
        return self.entity_config.numbers
    
    # ========== 服务方法 ==========
    
    async def add_feeding_item(
        self,
        day: int,
        time: str,
        amount: int,
        name: str,
        api_client: Any
    ) -> bool:
        """添加喂食计划项.
        
        Args:
            day: 星期几（1-7）
            time: 时间（HH:MM）
            amount: 出粮量
            name: 计划名称
            api_client: API 客户端
            
        Returns:
            是否成功
        """
        raise NotImplementedError(f"{self.model_name} 不支持添加喂食计划")
    
    async def update_feeding_item(
        self,
        day: int,
        item_id: str,
        time: str | None,
        amount: int | None,
        name: str | None,
        api_client: Any
    ) -> bool:
        """更新喂食计划项.
        
        Args:
            day: 星期几（1-7）
            item_id: 计划项 ID
            time: 时间（HH:MM）
            amount: 出粮量
            name: 计划名称
            api_client: API 客户端
            
        Returns:
            是否成功
        """
        raise NotImplementedError(f"{self.model_name} 不支持更新喂食计划")
    
    async def remove_feeding_item(
        self,
        day: int,
        item_id: str,
        api_client: Any
    ) -> bool:
        """删除喂食计划项.
        
        Args:
            day: 星期几（1-7）
            item_id: 计划项 ID
            api_client: API 客户端
            
        Returns:
            是否成功
        """
        raise NotImplementedError(f"{self.model_name} 不支持删除喂食计划")
    
    async def toggle_feeding_item(
        self,
        day: int,
        item_id: str,
        enabled: bool,
        api_client: Any
    ) -> bool:
        """启用/禁用喂食计划项.
        
        Args:
            day: 星期几（1-7）
            item_id: 计划项 ID
            enabled: 是否启用
            api_client: API 客户端
            
        Returns:
            是否成功
        """
        raise NotImplementedError(f"{self.model_name} 不支持切换喂食计划状态")
    
    async def manual_feed(
        self,
        amount: int,
        api_client: Any
    ) -> bool:
        """手动喂食.
        
        Args:
            amount: 出粮量
            api_client: API 客户端
            
        Returns:
            是否成功
        """
        raise NotImplementedError(f"{self.model_name} 不支持手动喂食")
    
    async def update_setting(
        self,
        key: str,
        value: int,
        api_client: Any
    ) -> bool:
        """更新设备设置.
        
        Args:
            key: 设置键
            value: 设置值
            api_client: API 客户端
            
        Returns:
            是否成功
        """
        raise NotImplementedError(f"{self.model_name} 不支持更新设置")
    
    async def get_photo(
        self,
        api_client: Any
    ) -> bytes | None:
        """获取照片（如果有摄像头）.
        
        Args:
            api_client: API 客户端
            
        Returns:
            照片数据
        """
        if not self.capabilities.supports_camera:
            raise NotImplementedError(f"{self.model_name} 不支持拍照")
        
        return None