"""API 频率限制器"""

import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

# API 频率限制配置
DEFAULT_REQUEST_INTERVAL = 10  # 默认请求间隔（秒）
WHITELIST_REQUEST_INTERVAL = 0  # 白名单请求间隔（秒）

# 白名单 API 端点（查询类 API，不做限制）
# 根据 API 文档整理：https://docs/petkit-d4-api.md
# 这些 API 只读数据，不会改变设备状态
RATE_LIMIT_WHITELIST = {
    # 认证相关
    "user/login",
    "user/refreshsession",
    "user/registerPushToken",
    
    # 设备查询
    "device/getPetkitDevices",
    "device/getDeviceServers",
    "d4/owndevices",
    "d4/device_detail",
    "d4/devicestate",
    "d4/refreshHomeV2",
    
    # 喂食相关查询
    "d4/feed",
    "d4/dailyFeeds",
    "d4/feedStatistic",
    "feederchart/feedStatistic",
    
    # 用户查询
    "user/details2",
    "user/unreadStatus",
    
    # 家庭查询
    "group/family/list",
    
    # OTA 检查
    "d4/ota_check",
}

# 以下 API 不在白名单，需要 6 秒限制：
# - d4/saveFeed: 保存喂食计划
# - d4/saveDailyFeed: 手动出粮
# - d4/removeDailyFeed: 删除/禁用喂食计划项
# - d4/restoreDailyFeed: 恢复喂食计划项
# - d4/updateSettings: 更新设备设置
# - d4/replenishedFood: 补粮确认
# - d4/desiccant_reset: 重置干燥剂
# - d4/calibration: 校准出粮量


def _is_whitelist_api(url: str) -> bool:
    """检查 API 是否在白名单中（不需要频率限制）.
    
    Args:
        url: API URL 或 endpoint
        
    Returns:
        True 表示在白名单中（不限制），False 表示需要限制
    """
    # 提取 endpoint（去掉域名和参数）
    # 例如：https://api.petkit.cn/device/detail -> device/detail
    endpoint = url.split("?")[0]  # 去掉查询参数
    endpoint = endpoint.rstrip("/")
    
    # 尝试从完整 URL 中提取 endpoint
    if "/" in endpoint:
        parts = endpoint.split("/")
        # 取最后两部分作为 endpoint（如 device/detail）
        if len(parts) >= 2:
            endpoint = "/".join(parts[-2:])
    
    # 检查是否在白名单中
    for whitelist_endpoint in RATE_LIMIT_WHITELIST:
        if endpoint.endswith(whitelist_endpoint) or endpoint == whitelist_endpoint:
            return True
    
    return False


class RateLimiter:
    """API 频率限制器.
    
    使用全局锁和上次请求时间来限制 API 调用频率。
    白名单内的 API 不受限制。
    """
    
    _instance = None
    _lock: asyncio.Lock | None = None
    _last_request_time: float | None = None
    
    def __new__(cls):
        """单例模式."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化频率限制器."""
        if self._lock is None:
            self._lock = asyncio.Lock()
            self._last_request_time = None
    
    async def throttle(self, url: str) -> None:
        """对 API 请求进行节流.
        
        Args:
            url: API URL
        """
        # 检查是否在白名单中
        is_whitelist = _is_whitelist_api(url)
        request_interval = WHITELIST_REQUEST_INTERVAL if is_whitelist else DEFAULT_REQUEST_INTERVAL
        
        if request_interval <= 0:
            return
        
        async with self._lock:
            now = asyncio.get_running_loop().time()
            
            if self._last_request_time is not None:
                # 距上次请求的时间差
                delta = now - self._last_request_time
                wait_for = request_interval - delta
                
                if wait_for > 0:
                    _LOGGER.debug(
                        "PetKit API 触发节流，等待 %.2f 秒后再发送请求 (endpoint: %s)",
                        wait_for,
                        url
                    )
                    await asyncio.sleep(wait_for)
            
            # 记录本次请求时间
            self._last_request_time = asyncio.get_running_loop().time()
    
    @classmethod
    def get_instance(cls) -> "RateLimiter":
        """获取单例实例."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance