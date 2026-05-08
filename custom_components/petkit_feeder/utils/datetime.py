"""日期时间处理工具函数"""

from datetime import datetime


def get_today_date() -> str:
    """获取今日日期字符串（YYYY-MM-DD）.
    
    Returns:
        日期字符串（如 "2026-04-01"）
    """
    now = datetime.now()
    return now.strftime("%Y-%m-%d")


def get_today_date_int() -> int:
    """获取今日日期整数（YYYYMMDD）.
    
    Returns:
        日期整数（如 20260401）
    """
    now = datetime.now()
    return int(now.strftime("%Y%m%d"))


def format_time_from_seconds(seconds: int) -> str:
    """将秒数转换为 HH:MM 格式.
    
    Args:
        seconds: 从 00:00 开始的秒数（如 21600 表示 06:00）
        
    Returns:
        时间字符串（如 "06:00"）
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours:02d}:{minutes:02d}"


def format_time_to_seconds(time_str: str) -> int:
    """将 HH:MM 格式转换为秒数.
    
    Args:
        time_str: 时间字符串（如 "06:00"）
        
    Returns:
        从 00:00 开始的秒数（如 21600）
    """
    try:
        parts = time_str.split(":")
        hours = int(parts[0])
        minutes = int(parts[1]) if len(parts) > 1 else 0
        return hours * 3600 + minutes * 60
    except (ValueError, IndexError):
        return 0


def parse_datetime_from_iso(iso_str: str) -> datetime | None:
    """解析 ISO 8601 格式的时间字符串.
    
    Args:
        iso_str: ISO 8601 格式字符串（如 "2026-03-09T22:00:20.000+0000"）
        
    Returns:
        datetime 对象，解析失败返回 None
    """
    try:
        # 处理 "+0000" 格式的时区
        if "+" in iso_str and not iso_str.endswith("Z"):
            iso_str = iso_str[:-5] + "+00:00"
        return datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None