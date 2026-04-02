"""服务 Schema 定义"""

import voluptuous as vol
from homeassistant.helpers import config_validation as cv

# 删除喂食计划 Schema
REMOVE_FEEDING_ITEM_SCHEMA = vol.Schema({
    vol.Optional("entry_id"): cv.string,
    vol.Required("day"): vol.All(vol.Coerce(int), vol.Range(min=1, max=7)),
    vol.Required("item_id"): cv.string,
})

# 切换喂食计划状态 Schema
TOGGLE_FEEDING_ITEM_SCHEMA = vol.Schema({
    vol.Optional("entry_id"): cv.string,
    vol.Required("day"): vol.All(vol.Coerce(int), vol.Range(min=1, max=7)),
    vol.Required("item_id"): cv.string,
    vol.Required("enabled"): cv.boolean,
})

# 批量保存喂食计划 Schema
SAVE_FEED_SCHEMA = vol.Schema({
    vol.Optional("entry_id"): cv.string,
    vol.Required("days"): cv.string,  # "1,2,3,4,5,6,7" 格式
    vol.Required("items"): vol.All(
        cv.ensure_list,
        [
            vol.Schema({
                vol.Required("time"): cv.string,  # HH:MM 格式
                vol.Required("amount"): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
                vol.Optional("name", default=""): cv.string,
                vol.Optional("enabled", default=True): cv.boolean,
            })
        ]
    ),
})

# 所有服务 Schema
SERVICE_SCHEMAS = {
    "remove_feeding_item": REMOVE_FEEDING_ITEM_SCHEMA,
    "toggle_feeding_item": TOGGLE_FEEDING_ITEM_SCHEMA,
    "save_feed": SAVE_FEED_SCHEMA,
}