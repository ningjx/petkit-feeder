"""D4 (Fresh Element Solo) 设备实现"""

from __future__ import annotations

from typing import Any

from .base import PetkitDevice, DeviceType, DeviceCapabilities, DeviceEntityConfig


class D4Device(PetkitDevice):
    """D4 (Fresh Element Solo) 喂食器设备.
    
    这是目前支持的主要设备型号。
    """
    
    @property
    def device_type(self) -> DeviceType:
        """设备类型."""
        return DeviceType.D4
    
    @property
    def model_name(self) -> str:
        """设备型号名称."""
        return "Fresh Element Solo"
    
    @property
    def capabilities(self) -> DeviceCapabilities:
        """设备能力配置."""
        return DeviceCapabilities(
            supports_schedule=True,
            supports_manual_feed=True,
            supports_feeding_history=True,
            supports_food_level=True,
            supports_camera=False,
            supports_desiccant=True,
            supports_voice=False,
            supports_calibration=True,
            supports_wifi_info=True,
            supports_real_amount_total=True,
            supports_plan_amount_total=True,
            supports_add_amount_total=True,
            supports_plan_real_amount_total=True,
        )
    
    @property
    def entity_config(self) -> DeviceEntityConfig:
        """设备实体配置."""
        return DeviceEntityConfig(
            sensors=[
                "device_name",
                "device_id",
                "last_feeding",
                "last_amount",
                "today_count",
                "feeding_schedule",
                "feeding_history",
            ],
            stat_sensors=[
                "real_amount_total",
                "plan_amount_total",
                "add_amount_total",
                "plan_real_amount_total",
            ],
            wifi_sensors=[
                "wifi_ssid",
                "wifi_rsq",
            ],
            binary_sensors=[
                "online",
            ],
            buttons=[
                "refresh",
                "manual_feed",
            ],
            switches=[
                "light_mode",
                "food_warn",
                "feed_notify",
                "manual_lock",
            ],
            numbers=[
                "feed_amount",
            ],
        )
    
    # ========== 服务实现 ==========
    
    async def add_feeding_item(
        self,
        day: int,
        time: str,
        amount: int,
        name: str,
        api_client: Any
    ) -> bool:
        """添加喂食计划项（D4 实现）."""
        # 解析时间
        time_parts = time.split(":")
        time_seconds = int(time_parts[0]) * 3600 + int(time_parts[1]) * 60
        
        # 构建 feedDailyList
        feed_daily_list = [{
            "count": 1,
            "items": [{
                "amount": amount,
                "amount1": 0,
                "amount2": 0,
                "deviceId": int(self._device_data.id),
                "deviceType": 11,
                "id": time_seconds,
                "name": name or f"周{day}喂食",
                "petAmount": [],
                "time": time_seconds,
            }],
            "repeats": str(day),
            "suspended": 0,
            "totalAmount": amount,
            "totalAmount1": 0,
            "totalAmount2": 0,
        }]
        
        # 调用 API
        await api_client.req.request(
            "POST",
            "d4/saveFeed",
            data={
                "deviceId": int(self._device_data.id),
                "feedDailyList": str(feed_daily_list),
            }
        )
        
        return True
    
    async def update_feeding_item(
        self,
        day: int,
        item_id: str,
        time: str | None,
        amount: int | None,
        name: str | None,
        api_client: Any
    ) -> bool:
        """更新喂食计划项（D4 实现）."""
        # D4 的更新逻辑：先删除再添加
        if item_id:
            await self.remove_feeding_item(day, item_id, api_client)
        
        if time and amount:
            await self.add_feeding_item(day, time, amount, name or "", api_client)
        
        return True
    
    async def remove_feeding_item(
        self,
        day: int,
        item_id: str,
        api_client: Any
    ) -> bool:
        """删除喂食计划项（D4 实现）."""
        # 获取今日日期
        from datetime import datetime
        today = int(datetime.now().strftime("%Y%m%d"))
        
        # 调用 API
        await api_client.req.request(
            "POST",
            f"d4/removeDailyFeed?id={item_id}&deviceId={self._device_data.id}&day={today}"
        )
        
        return True
    
    async def toggle_feeding_item(
        self,
        day: int,
        item_id: str,
        enabled: bool,
        api_client: Any
    ) -> bool:
        """启用/禁用喂食计划项（D4 实现）."""
        from datetime import datetime
        today = int(datetime.now().strftime("%Y%m%d"))
        
        if enabled:
            # 恢复计划项
            await api_client.req.request(
                "POST",
                f"d4/restoreDailyFeed?id={item_id}&deviceId={self._device_data.id}&day={today}"
            )
        else:
            # 禁用计划项
            await api_client.req.request(
                "POST",
                f"d4/removeDailyFeed?id={item_id}&deviceId={self._device_data.id}&day={today}"
            )
        
        return True
    
    async def manual_feed(
        self,
        amount: int,
        api_client: Any
    ) -> bool:
        """手动喂食（D4 实现）."""
        from datetime import datetime
        today = int(datetime.now().strftime("%Y%m%d"))
        
        await api_client.req.request(
            "POST",
            "d4/saveDailyFeed",
            data={
                "amount": amount,
                "time": -1,
                "deviceId": int(self._device_data.id),
                "day": today,
            }
        )
        
        return True
    
    async def update_setting(
        self,
        key: str,
        value: int,
        api_client: Any
    ) -> bool:
        """更新设备设置（D4 实现）."""
        import json
        from urllib.parse import quote
        
        kv_json = json.dumps({key: value})
        kv_encoded = quote(kv_json)
        
        await api_client.req.request(
            "POST",
            f"d4/updateSettings?kv={kv_encoded}&id={self._device_data.id}"
        )
        
        return True