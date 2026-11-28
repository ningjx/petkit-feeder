"""时区处理工具函数"""

from datetime import tzinfo
import logging

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from ..const import REGION_TIMEZONE_MAP, DEFAULT_TIMEZONE

_LOGGER = logging.getLogger(__name__)


def get_timezone_for_region(region: str) -> str:
    """根据地区获取时区字符串.
    
    Args:
        region: 地区代码（如 "CN", "US", "EU"）
        
    Returns:
        时区字符串（如 "Asia/Shanghai"）
    """
    return REGION_TIMEZONE_MAP.get(region, DEFAULT_TIMEZONE)


async def async_get_feeder_time_zone(hass: HomeAssistant, region: str) -> tzinfo:
    """Load the HA time zone, or the region default, once during entry setup."""
    name = hass.config.time_zone or get_timezone_for_region(region)
    if hasattr(dt_util, "async_get_time_zone"):
        zone = await dt_util.async_get_time_zone(name)
    else:
        # Earlier HA releases only provide the synchronous lookup.
        zone = await hass.async_add_executor_job(dt_util.get_time_zone, name)
    if zone is None:
        _LOGGER.warning("Unknown time zone %s, using UTC", name)
        return dt_util.UTC
    return zone
