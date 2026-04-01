"""缓存工具函数"""

from functools import lru_cache
from datetime import datetime


@lru_cache(maxsize=128)
def cached_format_time(seconds: int, date_key: str) -> str:
    """缓存的时间格式化函数.
    
    Args:
        seconds: 从 00:00 开始的秒数
        date_key: 日期键（用于缓存失效）
        
    Returns:
        格式化的时间字符串 HH:MM
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours:02d}:{minutes:02d}"


@lru_cache(maxsize=32)
def cached_get_weekday_name(weekday: int) -> str:
    """缓存的星期名称获取.
    
    Args:
        weekday: 星期几（1-7）
        
    Returns:
        星期名称
    """
    weekday_names = {
        1: "周一",
        2: "周二",
        3: "周三",
        4: "周四",
        5: "周五",
        6: "周六",
        7: "周日",
    }
    return weekday_names.get(weekday, "未知")


class DataCache:
    """数据缓存管理器.
    
    用于缓存设备数据和处理结果，减少重复计算。
    """
    
    def __init__(self):
        """初始化缓存."""
        self._cache: dict = {}
        self._last_update: datetime | None = None
    
    def get(self, key: str):
        """获取缓存值."""
        return self._cache.get(key)
    
    def set(self, key: str, value) -> None:
        """设置缓存值."""
        self._cache[key] = value
        self._last_update = datetime.now()
    
    def clear(self) -> None:
        """清空缓存."""
        self._cache.clear()
        self._last_update = None
    
    def is_valid(self, max_age_seconds: int = 60) -> bool:
        """检查缓存是否有效.
        
        Args:
            max_age_seconds: 最大有效期（秒）
            
        Returns:
            缓存是否有效
        """
        if not self._last_update:
            return False
        
        age = (datetime.now() - self._last_update).total_seconds()
        return age < max_age_seconds