"""喂食服务"""

import logging
from typing import Callable, Awaitable

from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse

from ..const import DOMAIN
from ..coordinator import PetkitDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class FeedingService:
    """喂食服务管理类.
    
    统一管理所有喂食相关服务的注册和处理。
    """
    
    def __init__(self, hass: HomeAssistant):
        """初始化喂食服务.
        
        Args:
            hass: Home Assistant 实例
        """
        self.hass = hass
    
    def _get_coordinator(self, entry_id: str | None) -> PetkitDataUpdateCoordinator:
        """获取协调器实例.
        
        Args:
            entry_id: 配置条目 ID（可选）
            
        Returns:
            协调器实例
            
        Raises:
            ValueError: 未找到协调器
        """
        if entry_id:
            return self.hass.data[DOMAIN][entry_id]
        
        for coord in self.hass.data[DOMAIN].values():
            return coord
        
        raise ValueError("未找到任何 PetKit 喂食器配置")
    
    def _create_handler(
        self,
        service_name: str,
        param_keys: list[str]
    ) -> Callable[[ServiceCall], Awaitable[ServiceResponse]]:
        """创建服务处理器.

        Args:
            service_name: 服务名称
            param_keys: 参数键列表

        Returns:
            异步服务处理函数
        """
        async def handler(call: ServiceCall) -> ServiceResponse:
            """服务处理函数."""
            coordinator = self._get_coordinator(call.data.get("entry_id"))

            # 提取参数
            params = {key: call.data[key] for key in param_keys if key in call.data}

            # 调用协调器方法
            method = getattr(coordinator, service_name)
            result = await method(**params)

            # 根据返回值记录日志
            success = result is not False
            if not success:
                _LOGGER.error("服务调用失败: %s", service_name)
            else:
                _LOGGER.info("服务调用成功: %s", service_name)

            return {"success": success, "service": service_name}

        return handler
    
    def register_services(self, schemas: dict) -> None:
        """注册所有服务.
        
        Args:
            schemas: 服务 Schema 字典
        """
        for service_name, schema in schemas.items():
            # 确定参数键
            if service_name == "save_feed":
                param_keys = ["weekly_plan"]
            elif service_name == "toggle_feeding_item":
                param_keys = ["day", "item_id", "enabled"]
            else:
                param_keys = []
            
            self.hass.services.async_register(
                DOMAIN,
                service_name,
                self._create_handler(service_name, param_keys),
                schema=schema,
            )
            
            _LOGGER.debug("已注册服务: %s", service_name)
    
    def unregister_services(self, service_names: list[str]) -> None:
        """注销服务.
        
        Args:
            service_names: 服务名称列表
        """
        for service_name in service_names:
            self.hass.services.async_remove(DOMAIN, service_name)
            _LOGGER.debug("已注销服务: %s", service_name)