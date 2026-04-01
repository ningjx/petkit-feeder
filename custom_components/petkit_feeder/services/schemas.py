"""服务 Schema 定义"""

import voluptuous as vol
from homeassistant.helpers import config_validation as cv

# 新增喂食计划 Schema
ADD_FEEDING_ITEM_SCHEMA = vol.Schema({
    vol.Optional("entry_id"): cv.string,
    vol.Required("day"): vol.All(vol.Coerce(int), vol.Range(min=1, max=7)),
    vol.Required("time"): cv.string,
    vol.Required("amount"): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
    vol.Optional("name", default=""): cv.string,
})

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

# 更新喂食计划 Schema
UPDATE_FEEDING_ITEM_SCHEMA = vol.Schema({
    vol.Optional("entry_id"): cv.string,
    vol.Required("day"): vol.All(vol.Coerce(int), vol.Range(min=1, max=7)),
    vol.Required("item_id"): cv.string,
    vol.Optional("time"): cv.string,
    vol.Optional("amount"): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
    vol.Optional("name"): cv.string,
})

# 所有服务 Schema
SERVICE_SCHEMAS = {
    "add_feeding_item": ADD_FEEDING_ITEM_SCHEMA,
    "remove_feeding_item": REMOVE_FEEDING_ITEM_SCHEMA,
    "toggle_feeding_item": TOGGLE_FEEDING_ITEM_SCHEMA,
    "update_feeding_item": UPDATE_FEEDING_ITEM_SCHEMA,
}