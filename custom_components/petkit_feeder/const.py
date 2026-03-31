"""常量定义."""

DOMAIN = "petkit_solo"

DEFAULT_NAME = "PetKit SOLO"

LOW_FOOD_THRESHOLD = 20

BUTTON_REFRESH = "refresh"

CONF_REFRESH_MODE = "refresh_mode"
CONF_REFRESH_INTERVAL = "refresh_interval"
REFRESH_MODE_AUTO = "auto"
REFRESH_MODE_MANUAL = "manual"

UPDATE_INTERVAL = 7200  # 2 小时
DEFAULT_REFRESH_INTERVAL = 7200
MIN_UPDATE_INTERVAL = 300  # 最小 5 分钟
MAX_UPDATE_INTERVAL = 86400  # 最大 24 小时

REGION_TIMEZONE_MAP = {
    "CN": "Asia/Shanghai",
    "US": "America/New_York",
    "EU": "Europe/Berlin",
    "JP": "Asia/Tokyo",
    "AU": "Australia/Sydney",
}
DEFAULT_TIMEZONE = "Asia/Shanghai"

PLAN_REFRESH_DELAY = 120  # 计划时间后延迟刷新的秒数