"""配置流程 - 用户配置集成."""

from __future__ import annotations

import logging
import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.core import callback
from .pypetkitapi.client import PetKitClient
from .pypetkitapi.exceptions import PetkitAuthenticationError, PypetkitError
from .pypetkitapi.feeder_container import Feeder

from .const import (
    DOMAIN,
    DEFAULT_NAME,
    CONF_REFRESH_MODE,
    CONF_REFRESH_INTERVAL,
    REFRESH_MODE_AUTO,
    REFRESH_MODE_MANUAL,
    DEFAULT_REFRESH_INTERVAL,
    MIN_UPDATE_INTERVAL,
    MAX_UPDATE_INTERVAL,
    REGION_LOCALE_MAP,
    DEFAULT_LOCALE,
)

_LOGGER = logging.getLogger(__name__)


class PetkitConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """小佩喂食器配置流程."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """初始化."""
        self._feeder_devices = []
        self._user_input = None
        self._owner_info = None  # 存储主账号信息

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> ConfigFlowResult:
        """处理用户配置步骤."""
        errors = {}

        if user_input is not None:
            # 验证账号密码
            try:
                # 创建临时 session 用于登录
                region = user_input.get("region", "CN")
                locale = REGION_LOCALE_MAP.get(region, DEFAULT_LOCALE)
                async with aiohttp.ClientSession() as session:
                    client = PetKitClient(
                        username=user_input["username"],
                        password=user_input["password"],
                        region=region,
                        timezone="Asia/Shanghai",
                        locale=locale,
                        session=session,
                    )
                    
                    # 登录
                    await client.login()
                    
                    # 获取设备列表
                    await client.get_devices_data()
                    
                    # 获取主账号信息（is_owner=1）
                    self._owner_info = self._get_owner_info(client)
                    
                    # 过滤 SOLO/喂食器设备
                    feeder_devices = []
                    for dev_id, device in client.petkit_entities.items():
                        if isinstance(device, Feeder):
                            device_name = device.name if hasattr(device, 'name') else f"喂食器 {dev_id}"
                            feeder_devices.append({
                                "id": str(dev_id),
                                "name": device_name,
                                "type": device.type if hasattr(device, 'type') else "feeder",
                            })
                    
                    if not feeder_devices:
                        errors["base"] = "no_devices"
                    else:
                        # 存储设备列表和用户输入，进入设备选择步骤
                        self._feeder_devices = feeder_devices
                        self._user_input = user_input  # 保存用户输入，用于后续保存 region
                        return await self.async_step_device()
                    
            except PetkitAuthenticationError:
                _LOGGER.error("认证失败")
                errors["base"] = "invalid_auth"
            except PypetkitError as err:
                _LOGGER.error("连接失败：%s", err)
                errors["base"] = "connection_failed"
            except Exception as e:
                _LOGGER.exception("未知错误：%s", e)
                errors["base"] = "unknown"

        # 获取之前输入的值（用于错误时保留表单数据）
        username = user_input.get("username", "") if user_input else ""
        password = user_input.get("password", "") if user_input else ""
        region = user_input.get("region", "CN") if user_input else "CN"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("username", default=username): str,
                    vol.Required("password", default=password): str,
                    vol.Optional("region", default=region): vol.In(
                        {
                            "CN": "中国大陆",
                            "US": "美国",
                            "EU": "欧洲",
                        }
                    ),
                }
            ),
            errors=errors,
        )

    def _get_owner_info(self, client: PetKitClient) -> dict | None:
        """获取主账号信息（is_owner=1）."""
        try:
            for account in client.account_data:
                if account.user_list:
                    for user in account.user_list:
                        if user.is_owner == 1:
                            return {
                                "user_name": user.user_name or "未知用户",
                                "user_id": user.user_id or 0,
                            }
        except Exception as e:
            _LOGGER.warning("获取主账号信息失败：%s", e)
        return None

    async def async_step_device(
        self, user_input: dict | None = None
    ) -> ConfigFlowResult:
        """处理设备选择步骤."""
        if user_input is not None:
            return await self._async_create_entry(user_input["device_id"])

        # 显示设备列表
        device_options = {d["id"]: d["name"] for d in self._feeder_devices}
        
        return self.async_show_form(
            step_id="device",
            data_schema=vol.Schema(
                {
                    vol.Required("device_id"): vol.In(device_options),
                }
            ),
            description_placeholders={
                "device_count": len(self._feeder_devices),
            },
        )

    async def _async_create_entry(
        self,
        device_id: str,
    ) -> ConfigFlowResult:
        """创建配置条目."""
        # 获取选中的设备名称
        device_name = DEFAULT_NAME
        for device in self._feeder_devices:
            if device["id"] == device_id:
                device_name = device["name"]
                break
        
        # 构建配置条目标题：显示用户信息
        if self._owner_info:
            title = f"{self._owner_info['user_name']} (ID: {self._owner_info['user_id']})"
        else:
            title = DEFAULT_NAME
        
        _LOGGER.info("配置成功，用户：%s，设备：%s (ID: %s)", 
                     title, device_name, device_id)
        
        return self.async_create_entry(
            title=title,
            data={
                "username": self._user_input["username"],
                # 存储密码以便后续协调器登录使用
                # 如果以后要更安全的做法，可以考虑改成使用刷新 token 或让用户在选项里重新输入
                "password": self._user_input["password"],
                "device_id": device_id,
                "device_name": device_name,  # 存储设备名称
                "region": self._user_input.get("region", "CN"),  # 使用用户选择的 region
                "user_name": self._owner_info.get("user_name") if self._owner_info else None,
                "user_id": self._owner_info.get("user_id") if self._owner_info else None,
            },
            options={
                CONF_REFRESH_MODE: REFRESH_MODE_AUTO,
                CONF_REFRESH_INTERVAL: DEFAULT_REFRESH_INTERVAL,
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> PetkitOptionsFlowHandler:
        """获取选项流程."""
        return PetkitOptionsFlowHandler()


class PetkitOptionsFlowHandler(config_entries.OptionsFlow):
    """小佩喂食器选项流程."""

    async def async_step_init(
        self, user_input: dict | None = None
    ) -> ConfigFlowResult:
        """管理选项."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # 获取当前配置
        refresh_mode = self.config_entry.options.get(
            CONF_REFRESH_MODE, REFRESH_MODE_AUTO
        )
        refresh_interval = self.config_entry.options.get(
            CONF_REFRESH_INTERVAL, DEFAULT_REFRESH_INTERVAL,
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_REFRESH_MODE,
                        default=refresh_mode,
                    ): vol.In(
                        {
                            REFRESH_MODE_AUTO: "定时刷新",
                            REFRESH_MODE_MANUAL: "手动刷新",
                        }
                    ),
                    vol.Required(
                        CONF_REFRESH_INTERVAL,
                        default=refresh_interval,
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(
                            min=MIN_UPDATE_INTERVAL,
                            max=MAX_UPDATE_INTERVAL,
                        ),
                    ),
                }
            ),
            description_placeholders={
                "min_interval": MIN_UPDATE_INTERVAL,
                "max_interval": MAX_UPDATE_INTERVAL,
            },
        )
