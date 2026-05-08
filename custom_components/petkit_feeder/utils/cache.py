"""缓存工具函数"""

from datetime import datetime


# 多语言状态文本映射
STATUS_TEXTS: dict[str, dict[str, str]] = {
    "en": {
        "offline": "Offline",
        "no_plan": "No Plan",
        "no_feeding_today": "No feeding today",
        "no_records": "No records",
    },
    "zh": {
        "offline": "离线",
        "no_plan": "无计划",
        "no_feeding_today": "今日无待喂食",
        "no_records": "无记录",
    },
}


def get_status_text(key: str, language: str = "en") -> str:
    """获取状态文本（多语言支持）.

    Args:
        key: 状态文本 key（如 "offline", "no_plan"）
        language: 语言代码（"en" 或 "zh"）

    Returns:
        状态文本
    """
    lang_key = "zh" if language.startswith("zh") else "en"
    texts = STATUS_TEXTS.get(lang_key, STATUS_TEXTS["en"])
    return texts.get(key, key)


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