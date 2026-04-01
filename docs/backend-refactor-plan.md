# 后端代码重构方案

## 目标

1. **架构更清晰**：模块化设计，职责分离
2. **易读性**：代码组织清晰，快速定位功能
3. **易扩展**：支持后续扩展更多型号喂食器（D3、D4、D4S、Mini 等）
4. **多语言**：完善国际化支持
5. **性能优化**：减少重复代码，优化数据处理

## 现状分析

### 当前文件结构

```
custom_components/petkit_feeder/
├── __init__.py           (166 行)  - 集成入口、服务注册
├── config_flow.py        (233 行)  - 配置流程
├── coordinator.py        (1371 行) - 数据协调器 ❌ 过大
├── sensor.py             (620 行)  - 传感器实体 ❌ 较大
├── binary_sensor.py      (173 行)  - 二进制传感器
├── button.py             (141 行)  - 按钮实体
├── number.py             (92 行)   - 数字输入实体
├── switch.py             (206 行)  - 开关实体
├── const.py              (30 行)   - 常量定义
└── pypetkitapi/          (禁止修改) - API 库
```

### 代码行数统计

| 文件 | 行数 | 问题 |
|-----|------|------|
| coordinator.py | 1371 | ❌ 过大，职责混杂 |
| sensor.py | 620 | ⚠️ 较大，有重复代码 |
| __init__.py | 166 | ⚠️ 服务处理代码重复 |
| config_flow.py | 233 | ✅ 正常 |
| switch.py | 206 | ✅ 正常 |
| binary_sensor.py | 173 | ✅ 正常 |
| button.py | 141 | ✅ 正常 |
| number.py | 92 | ✅ 正常 |

### 主要问题

1. **coordinator.py 过大（1371 行）**
   - 数据更新逻辑
   - 喂食计划处理
   - 设置更新
   - API 频率限制
   - 时区处理
   - 计划刷新调度

2. **缺乏设备型号抽象层**
   - 当前只支持 D4 设备
   - 硬编码了设备类型判断
   - 扩展新设备需要大量修改

3. **实体类有重复代码**
   - `device_info` 属性重复
   - `_get_device()` 方法重复
   - 初始化逻辑重复

4. **服务处理代码重复**
   - `_handle_xxx` 和 `_handle_xxx_wrapper` 模式重复
   - 日志记录格式不统一

5. **多语言支持不完善**
   - 翻译文件存在但未充分利用
   - 错误消息硬编码

## 重构方案

### 目标文件结构

```
custom_components/petkit_feeder/
├── __init__.py                    # 集成入口（精简后 ~80 行）
├── config_flow.py                 # 配置流程（保持不变）
├── const.py                       # 常量定义（扩充）
│
├── models/                        # 设备型号抽象层
│   ├── __init__.py
│   ├── base.py                    # 设备基类
│   ├── d3.py                      # D3 设备实现
│   ├── d4.py                      # D4 设备实现
│   ├── d4s.py                     # D4S 设备实现
│   ├── mini.py                    # Mini 设备实现
│   └── factory.py                 # 设备工厂
│
├── coordinators/                  # 数据协调器模块
│   ├── __init__.py
│   ├── base.py                    # 基础协调器
│   ├── feeder.py                  # 喂食器协调器
│   └── rate_limiter.py            # API 频率限制器
│
├── entities/                      # 实体基类模块
│   ├── __init__.py
│   ├── base.py                    # 实体基类
│   ├── sensor.py                  # 传感器基类
│   ├── binary_sensor.py           # 二进制传感器基类
│   ├── button.py                  # 按钮基类
│   ├── switch.py                  # 开关基类
│   └── number.py                  # 数字输入基类
│
├── services/                      # 服务模块
│   ├── __init__.py
│   ├── feeding.py                 # 喂食计划服务
│   ├── device.py                  # 设备服务
│   └── schemas.py                 # 服务 Schema 定义
│
├── utils/                         # 工具模块
│   ├── __init__.py
│   ├── timezone.py                # 时区处理
│   ├── datetime.py                # 日期时间处理
│   └── validation.py              # 数据验证
│
├── translations/                  # 翻译文件
│   ├── en.json
│   ├── zh.json
│   └── zh-Hans.json
│
└── pypetkitapi/                   # API 库（禁止修改）
```

### 模块职责划分

#### 1. models/ - 设备型号抽象层

**目的**：支持多型号喂食器，隔离设备差异

```python
# models/base.py
class BaseFeederDevice(ABC):
    """喂食器设备基类"""
    
    @property
    @abstractmethod
    def device_type(self) -> str:
        """设备类型标识（如 'd4', 'd3'）"""
        pass
    
    @property
    @abstractmethod
    def supported_features(self) -> set[str]:
        """支持的功能集"""
        pass
    
    @abstractmethod
    def parse_schedule(self, data: dict) -> FeedingSchedule:
        """解析喂食计划"""
        pass
    
    @abstractmethod
    def parse_records(self, data: dict) -> list[FeedingRecord]:
        """解析喂食记录"""
        pass

# models/d4.py
class D4FeederDevice(BaseFeederDevice):
    """D4 (Fresh Element Solo) 设备实现"""
    
    device_type = "d4"
    supported_features = {"schedule", "records", "manual_feed", "settings"}
    
    def parse_schedule(self, data: dict) -> FeedingSchedule:
        # D4 特有的解析逻辑
        pass
```

#### 2. coordinators/ - 数据协调器模块

**目的**：拆分 coordinator.py，职责单一

```python
# coordinators/base.py
class BaseCoordinator(DataUpdateCoordinator):
    """基础协调器"""
    
    def __init__(self, hass, device: BaseFeederDevice, ...):
        self.device = device
        self.rate_limiter = RateLimiter()
    
    async def _async_update_data(self):
        # 通用更新逻辑
        pass

# coordinators/feeder.py
class FeederCoordinator(BaseCoordinator):
    """喂食器协调器"""
    
    async def add_feeding_item(self, day, time, amount, name):
        # 添加喂食计划
        pass
    
    async def remove_feeding_item(self, day, item_id):
        # 删除喂食计划
        pass

# coordinators/rate_limiter.py
class RateLimiter:
    """API 频率限制器"""
    
    WHITELIST = {...}
    DEFAULT_INTERVAL = 6
    
    async def throttle(self, endpoint: str):
        # 节流逻辑
        pass
```

#### 3. entities/ - 实体基类模块

**目的**：消除重复代码，统一实体行为

```python
# entities/base.py
class PetkitEntity(CoordinatorEntity):
    """PetKit 实体基类"""
    
    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator)
        self._device_id = coordinator.device_id
    
    @property
    def device_info(self):
        """统一的设备信息"""
        device = self._get_device()
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": device.name if device else DEFAULT_NAME,
            "manufacturer": "Petkit",
            "model": device.device_nfo.modele_name if device else "Unknown",
        }
    
    def _get_device(self):
        """获取设备数据"""
        return self.coordinator.data.get("device_info")

# entities/sensor.py
class PetkitSensorEntity(PetkitEntity, SensorEntity):
    """传感器基类"""
    
    _attr_has_entity_name = True
    
    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{self._device_id}_{self.translation_key}"
        self.entity_id = f"sensor.petkit_feeder_{self._device_id}_{self.translation_key}"
```

#### 4. services/ - 服务模块

**目的**：统一服务注册和处理

```python
# services/schemas.py
SERVICE_SCHEMAS = {
    "add_feeding_item": vol.Schema({
        vol.Optional("entry_id"): cv.string,
        vol.Required("day"): vol.All(vol.Coerce(int), vol.Range(min=1, max=7)),
        vol.Required("time"): cv.string,
        vol.Required("amount"): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
        vol.Optional("name", default=""): cv.string,
    }),
    # ...
}

# services/feeding.py
class FeedingService:
    """喂食服务"""
    
    def __init__(self, hass: HomeAssistant):
        self.hass = hass
    
    async def register(self):
        """注册服务"""
        for name, schema in SERVICE_SCHEMAS.items():
            self.hass.services.async_register(
                DOMAIN, name, self._create_handler(name), schema=schema
            )
    
    def _create_handler(self, service_name: str):
        """创建服务处理器（消除重复的 wrapper 模式）"""
        async def handler(call: ServiceCall):
            coordinator = self._get_coordinator(call.data.get("entry_id"))
            method = getattr(coordinator, service_name)
            await method(**self._extract_params(call.data))
            _LOGGER.info("服务调用成功: %s", service_name)
        return handler
```

#### 5. utils/ - 工具模块

**目的**：复用工具函数

```python
# utils/timezone.py
def get_timezone_for_region(region: str) -> str:
    """根据地区获取时区"""
    return REGION_TIMEZONE_MAP.get(region, DEFAULT_TIMEZONE)

# utils/datetime.py
def get_today_weekday() -> int:
    """获取今天是周几（1-7）"""
    day = datetime.now().weekday()
    return day + 1 if day != 6 else 7

def format_time_from_seconds(seconds: int) -> str:
    """将秒数转换为 HH:MM 格式"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours:02d}:{minutes:02d}"
```

### 设备型号扩展设计

#### 枚举设备型号

```python
# const.py
class DeviceModel(Enum):
    """支持的设备型号"""
    D3 = "d3"       # PetKit D3
    D4 = "d4"       # Fresh Element Solo
    D4S = "d4s"     # Fresh Element Solo (升级版)
    MINI = "mini"   # PetKit Mini

DEVICE_MODEL_MAP = {
    "d3": DeviceModel.D3,
    "d4": DeviceModel.D4,
    "d4s": DeviceModel.D4S,
    "feeder_mini": DeviceModel.MINI,
}
```

#### 设备工厂

```python
# models/factory.py
class DeviceFactory:
    """设备工厂"""
    
    @staticmethod
    def create(device_type: str, api_data: dict) -> BaseFeederDevice:
        """根据设备类型创建设备实例"""
        model = DEVICE_MODEL_MAP.get(device_type.lower())
        
        if model == DeviceModel.D4:
            return D4FeederDevice(api_data)
        elif model == DeviceModel.D3:
            return D3FeederDevice(api_data)
        elif model == DeviceModel.MINI:
            return MiniFeederDevice(api_data)
        else:
            raise UnsupportedDeviceError(f"不支持的设备类型: {device_type}")
```

### 多语言支持设计

#### 翻译键定义

```json
// translations/zh-Hans.json
{
  "config": {
    "step": {
      "user": {
        "title": "登录 PetKit 账号",
        "data": {
          "username": "手机号",
          "password": "密码",
          "region": "地区"
        }
      }
    },
    "error": {
      "invalid_auth": "用户名或密码错误",
      "connection_failed": "连接失败"
    }
  },
  "services": {
    "add_feeding_item": {
      "name": "新增喂食计划",
      "description": "添加一个新的喂食计划项",
      "fields": {
        "day": {"name": "星期", "description": "1-7 表示周一到周日"},
        "time": {"name": "时间", "description": "喂食时间，格式 HH:MM"}
      }
    }
  }
}
```

#### 使用翻译

```python
# 获取翻译文本
from homeassistant.helpers.translation import async_get_translations

async def get_localized_message(hass, key: str) -> str:
    """获取本地化消息"""
    translations = await async_get_translations(hass, hass.config.language, "common", DOMAIN)
    return translations.get(f"component.{DOMAIN}.{key}", key)
```

## 执行步骤

### 阶段 1：创建基础模块（低风险）

**预估时间**：2 小时

1. **创建 utils/ 模块**
   - 提取 `timezone.py`：时区处理函数
   - 提取 `datetime.py`：日期时间处理函数
   - 更新 `coordinator.py` 和其他文件的导入

2. **创建 entities/base.py**
   - 提取 `PetkitEntity` 基类
   - 统一 `device_info` 属性
   - 统一 `_get_device()` 方法

3. **验证测试**
   - 运行 HA，确认功能正常
   - 检查日志无错误

### 阶段 2：提取实体基类（低风险）

**预估时间**：1.5 小时

1. **创建 entities/sensor.py**
   - 提取 `PetkitSensorEntity` 基类
   - 更新 `sensor.py` 使用基类

2. **创建 entities/binary_sensor.py**
   - 提取 `PetkitBinarySensorEntity` 基类
   - 更新 `binary_sensor.py` 使用基类

3. **创建 entities/button.py、entities/switch.py、entities/number.py**
   - 同上

4. **验证测试**
   - 检查所有实体是否正常工作

### 阶段 3：拆分 coordinator（中等风险）

**预估时间**：3 小时

1. **创建 coordinators/rate_limiter.py**
   - 提取 API 频率限制逻辑
   - 移动白名单配置

2. **创建 coordinators/base.py**
   - 提取基础协调器逻辑
   - 时区初始化
   - 会话管理

3. **创建 coordinators/feeder.py**
   - 继承 `BaseCoordinator`
   - 喂食计划相关方法
   - 数据更新逻辑

4. **更新 `coordinator.py`**
   - 改为导入 `FeederCoordinator` 的别名
   - 或保留兼容层

5. **验证测试**
   - 数据更新正常
   - 喂食计划操作正常

### 阶段 4：创建设备型号抽象层（中等风险）

**预估时间**：3 小时

1. **创建 models/base.py**
   - 定义 `BaseFeederDevice` 抽象基类
   - 定义设备能力接口

2. **创建 models/d4.py**
   - 实现 D4 设备类
   - 迁移 D4 特有的解析逻辑

3. **创建 models/factory.py**
   - 实现设备工厂
   - 根据设备类型创建实例

4. **更新协调器使用设备模型**
   - 注入设备实例
   - 使用设备模型的方法

5. **验证测试**
   - D4 设备功能正常

### 阶段 5：重构服务模块（低风险）

**预估时间**：1.5 小时

1. **创建 services/schemas.py**
   - 提取所有服务 Schema 定义

2. **创建 services/feeding.py**
   - 创建 `FeedingService` 类
   - 统一服务处理逻辑
   - 消除重复的 wrapper 函数

3. **更新 `__init__.py`**
   - 使用新的服务模块
   - 精简代码

4. **验证测试**
   - 服务调用正常

### 阶段 6：完善多语言支持（低风险）

**预估时间**：1 小时

1. **扩充翻译文件**
   - 添加服务描述翻译
   - 添加错误消息翻译

2. **更新代码使用翻译**
   - 服务描述
   - 错误消息

3. **验证测试**
   - 切换语言测试

### 阶段 7：性能优化（低风险）

**预估时间**：1 小时

1. **优化数据处理**
   - 使用缓存减少重复计算
   - 延迟加载非必要数据

2. **优化实体更新**
   - 精细化 `should_update` 逻辑
   - 减少不必要的渲染

3. **验证测试**
   - 性能测试
   - 内存占用测试

## 风险评估

| 阶段 | 风险 | 原因 | 缓解措施 |
|-----|------|------|---------|
| 阶段 1 | 低 | 只提取工具函数 | 保持函数签名不变 |
| 阶段 2 | 低 | 只提取基类 | 保持接口兼容 |
| 阶段 3 | 中 | coordinator 是核心 | 分步提取，每步测试 |
| 阶段 4 | 中 | 新增抽象层 | 保持向后兼容 |
| 阶段 5 | 低 | 只重构服务逻辑 | 保持服务签名不变 |
| 阶段 6 | 低 | 只增加翻译 | 不修改逻辑 |
| 阶段 7 | 低 | 只优化性能 | 不修改功能 |

## 验收标准

### 代码质量

- [ ] coordinator.py < 400 行
- [ ] sensor.py < 300 行
- [ ] __init__.py < 100 行
- [ ] 所有文件 < 500 行
- [ ] 无重复代码块

### 架构质量

- [ ] 模块职责单一
- [ ] 依赖关系清晰
- [ ] 无循环依赖
- [ ] 易于扩展新设备型号

### 功能完整性

- [ ] 所有原有功能保持不变
- [ ] 所有服务调用正常
- [ ] 所有实体正常工作
- [ ] 多语言切换正常

### 性能

- [ ] 数据更新响应 < 5 秒
- [ ] 服务调用响应 < 2 秒
- [ ] 内存占用无明显增加

## 后续扩展指南

### 添加新设备型号

1. 在 `models/` 创建新文件（如 `d5.py`）
2. 继承 `BaseFeederDevice`
3. 实现所有抽象方法
4. 在 `DeviceModel` 枚举添加型号
5. 在 `DeviceFactory` 添加创建逻辑

### 添加新功能

1. 在 `BaseFeederDevice` 定义接口
2. 在各设备型号实现
3. 在协调器调用设备方法
4. 在实体展示数据

## 时间估算

| 阶段 | 工时 | 累计 |
|-----|------|------|
| 阶段 1 | 2h | 2h |
| 阶段 2 | 1.5h | 3.5h |
| 阶段 3 | 3h | 6.5h |
| 阶段 4 | 3h | 9.5h |
| 阶段 5 | 1.5h | 11h |
| 阶段 6 | 1h | 12h |
| 阶段 7 | 1h | 13h |
| **总计** | **13h** | |

## 备注

- 每个阶段完成后提交代码
- 高风险阶段（阶段 3、4）需要充分测试
- 可根据实际情况调整执行顺序
- 禁止修改 `pypetkitapi/` 目录下的代码