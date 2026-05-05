# PetKit Feeder Home Assistant Integration

自定义集成，用于控制 PetKit（小佩）智能喂食器设备。

## 技术栈

- Python 3.11+ (Home Assistant 集成)
- TypeScript + Lit (前端 Lovelace 卡片，子项目 `petkit_feeder_card/`)
- aiohttp (异步 HTTP 请求)
- Pydantic (数据验证)

## 项目结构

```
petkit-feeder/                          # 主仓库（Git）
├── custom_components/petkit_feeder/    # Home Assistant 集成
│   ├── __init__.py                     # 集成入口
│   ├── config_flow.py                  # UI 配置流程
│   ├── coordinator.py                  # 数据更新协调器
│   ├── const.py                        # 常量定义
│   ├── manifest.json                   # 集成元数据
│   ├── devices/                        # 设备型号（工厂模式）
│   │   ├── base.py                     # 抽象基类 + 能力配置
│   │   ├── d4.py                       # D4 实现
│   │   └── factory.py                  # 设备工厂
│   ├── entities/                       # HA 实体
│   │   ├── sensor.py                   # 传感器
│   │   ├── switch.py                   # 开关
│   │   ├── button.py                   # 按钮
│   │   └ number.py                    # 数字输入
│   ├── pypetkitapi/                    # PetKit API 客户端
│   │   ├── client.py                   # API 核心
│   │   ├── feeder_container.py         # 数据容器
│   │   └── const.py                    # API 常量
│   ├── services/                       # 自定义服务
│   │   ├── feeding.py                  # 服务注册
│   │   └ schemas.py                   # 参数 Schema
│   ├── coordinators/
│   │   └ rate_limiter.py               # API 频率限制
│   ├── translations/                   # 多语言
│   └ utils/                            # 工具函数
│
├── petkit_feeder_card/                 # 前端卡片（Git Submodule）
│   ├── src/
│   │   ├── petkit-feeder-card.ts       # 主组件
│   │   ├── editor.ts                   # YAML 编辑器配置
│   │   ├── types.ts                    # 类型定义
│   │   ├── data/                       # 数据解析处理
│   │   ├── services/                   # HA 服务调用封装
│   │   ├── state/                      # 缓存管理、变更检测
│   │   ├── handlers/                   # 事件处理
│   │   ├── styles/                     # CSS 样式
│   │   ├── localize/                   # 多语言文本
│   │   └ utils/                        # 工具函数
│   ├── dist/                           # 编译输出
│   │   └ petkit-feeder-card.js
│   ├── hacs.json                       # 前端 HACS 配置
│   ├── package.json                    # npm 配置
│   └ tsconfig.json                    # TypeScript 配置
│
├── docs/                               # 文档图片
├── scripts/                            # 构建脚本
├── hacs.json                           # 后端 HACS 配置
├── README.md                           # 项目说明
├── CHANGELOG.md                        # 更新日志
├── .gitmodules                         # Submodule 配置
└ CLAUDE.md                            # 本文件
```

> **注意**：`petkit_feeder_card/` 是 Git Submodule，指向独立仓库 `https://github.com/ningjx/petkit-feeder-card.git`

## 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 文件名 | snake_case | `coordinator.py`, `rate_limiter.py` |
| 类名 | PascalCase | `PetkitDataUpdateCoordinator`, `D4Device` |
| 变量/函数 | snake_case | `device_id`, `async_update_data` |
| 常量 | UPPER_CASE | `DOMAIN`, `UPDATE_INTERVAL`, `DEFAULT_TIMEOUT` |
| 私有成员 | 前缀 `_` | `_LOGGER`, `_device`, `_async_setup` |
| 异步函数 | 前缀 `async_` | `async_setup_entry`, `async_manual_feed` |

## 代码风格

### Python

```python
# 文件头部导入
from __future__ import annotations

import logging
from typing import Any

_LOGGER = logging.getLogger(__name__)

# 类型注解必须完整
async def save_feed(
    self,
    days: list[int],
    items: list[dict[str, Any]],
    api_client: PetKitClient,
) -> bool:
    """保存喂食计划.

    Args:
        days: 周几列表 (1-7)
        items: 计划项列表

    Returns:
        是否成功
    """
    ...
```

### 日志规范

```python
_LOGGER.debug("获取设备数据: %s", device_id)      # 详细调试信息
_LOGGER.info("手动喂食成功: %dg", amount)         # 重要操作结果
_LOGGER.warning("API 调用失败: %s", error)        # 可恢复的问题
_LOGGER.error("设备离线: %s", device_id)          # 需关注的错误
```

### 异步规范

- 所有 API 调用和网络请求必须使用 `async/await`
- 避免在异步函数中使用 `time.sleep()`，改用 `asyncio.sleep()`
- 并发任务使用 `asyncio.gather()` 批量执行
- 锁使用 `asyncio.Lock()` 而非 `threading.Lock()`

## Home Assistant 集成模式

### Entity 规范

```python
class PetkitSensorEntity(CoordinatorEntity, SensorEntity):
    """传感器实体."""

    _attr_has_entity_name = True  # 必须，让 HA 自动组合设备名
    entity_description: PetkitSensorEntityDescription

    def __init__(
        self,
        coordinator: PetkitDataUpdateCoordinator,
        description: PetkitSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{description.key}"
```

### Coordinator 规范

```python
class PetkitDataUpdateCoordinator(DataUpdateCoordinator):
    """数据更新协调器."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.entry = entry

    async def _async_update_data(self) -> dict:
        """获取最新数据."""
        try:
            await self.api.get_devices_data()
            return {"devices": self.api.petkit_entities}
        except PetkitAuthenticationError:
            raise ConfigEntryAuthFailed("认证失败，请重新登录")
        except PetkitTimeoutError as err:
            raise UpdateFailed(f"连接超时: {err}")
```

### Service 规范

```python
# 在 async_setup 中注册服务（而非 async_setup_entry）
async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    hass.services.async_register(
        DOMAIN,
        "manual_feed",
        async_manual_feed_service,
        schema=MANUAL_FEED_SCHEMA,
    )
    return True

# 服务实现
async def async_manual_feed_service(call: ServiceCall) -> ServiceResponse:
    """手动喂食服务."""
    entry_id = call.data.get("entry_id")
    amount = call.data.get("amount")
    ...
    return {"success": True}  # 必须返回 JSON 可序列化的 dict
```

### Config Flow 规范

```python
class PetkitConfigFlow(ConfigFlow, domain=DOMAIN):
    """配置流程."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> ConfigFlowResult:
        """用户配置步骤."""
        errors: dict[str, str] = {}

        if user_input:
            # 验证输入
            try:
                await self._validate_login(user_input)
            except PetkitAuthenticationError:
                errors["base"] = "auth_failed"

            if not errors:
                # 使用唯一 ID 防止重复配置
                await self.async_set_unique_id(user_input["username"])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="PetKit", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=SCHEMA,
            errors=errors,
        )
```

## 设计模式

### 设备工厂模式

```python
# devices/factory.py
def create_device(device_data: dict) -> PetkitDevice:
    """根据设备类型创建设备实例."""
    device_type = device_data.get("type")
    if device_type == "d4":
        return D4Device(device_data)
    elif device_type == "d3":
        return D3Device(device_data)
    raise ValueError(f"未知设备类型: {device_type}")
```

### 能力配置模式

```python
@dataclass
class DeviceCapabilities:
    """设备能力配置."""
    supports_schedule: bool = True
    supports_manual_feed: bool = True
    supports_camera: bool = False
```

### 单例模式 (rate_limiter)

```python
class RateLimiter:
    """API 频率限制器 - 全局单例."""
    _instance: RateLimiter | None = None
    _lock: asyncio.Lock = asyncio.Lock()

    @classmethod
    async def get_instance(cls) -> RateLimiter:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
```

## API 频率限制

PetKit API 有调用频率限制，操作类 API 需间隔 10 秒：

```python
# 白名单 API（查询类，无限制）
WHITELIST_APIS = [
    "device_detail",
    "feeding_record",
    "get_daily_feed",
]

# 非白名单 API（操作类，需排队）
async def throttle(self, url: str) -> None:
    if url not in WHITELIST_APIS:
        await asyncio.sleep(10)  # 间隔 10 秒
```

## 前端卡片规范

前端卡片位于 `petkit_feeder_card/` 子项目，使用 TypeScript + Lit + Web Components。

### 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 文件名 | kebab-case 或 camelCase | `petkit-feeder-card.ts`, `diff-detector.ts` |
| 类名/组件名 | PascalCase | `PetkitFeederCard`, `WeeklyCacheManager` |
| 方法名 | camelCase，私有前缀 `_` | `_handleToggle`, `processWeeklyData` |
| 属性名 | camelCase，私有前缀 `_` | `_weeklyCache`, `_selectedDay` |
| 常量 | UPPER_CASE | `UPDATE_INTERVAL`, `DEFAULT_AMOUNT` |
| Custom Element | kebab-case | `'petkit-feeder-card'` |

### 代码风格

```typescript
// 组件命名：PascalCase，装饰器注册
@customElement('petkit-feeder-card')
export class PetkitFeederCard extends LitElement {
  // 私有属性：前缀 _
  @property({ attribute: false }) public hass!: HomeAssistant;
  @property({ attribute: false }) private _config?: PetkitSoloCardConfig;
  
  private _weeklyCache: WeeklyCacheManager = new WeeklyCacheManager();
  private _selectedDay: number = 1;
  private _isSaving: boolean = false;

  // 方法命名：camelCase，私有前缀 _
  private async _handleToggle(item: TimelineItem): Promise<void> {
    // 乐观更新：先改缓存更新 UI，后调用 API
    const dayCache = this._weeklyCache.getDayCache(this._selectedDay);
    if (dayCache) {
      const timelineItem = dayCache.timeline.find(t => t.itemId === item.itemId);
      if (timelineItem) {
        timelineItem.isEnabled = !item.isEnabled;
      }
    }
    this.requestUpdate();  // 立即刷新 UI
    
    try {
      await this.hass.callService('petkit_feeder', 'toggle_feeding_item', {...});
      this._weeklyCache.commit();  // 成功：提交缓存
    } catch (error) {
      this._weeklyCache.rollback();  // 失败：回滚缓存
    }
  }
  
  // 防抖处理
  private _saveDebounceTimer: number | null = null;
  
  private _triggerSaveDebounce(): void {
    if (this._saveDebounceTimer) {
      clearTimeout(this._saveDebounceTimer);
    }
    this._saveDebounceTimer = window.setTimeout(() => {
      this._triggerSave();
    }, 5000);  // 5 秒防抖
  }
}

// 服务调用封装
export async function saveFeed(
  hass: HomeAssistant,
  changedDays: ChangedDay[],
  weeklyCache: WeeklyCacheManager,
): Promise<void> {
  await hass.callService('petkit_feeder', 'save_feed', {
    weekly_plan: changedDays.map(day => ({
      day: day.day,
      suspended: 0,
      items: day.items,
    })),
  });
}
```

### Lit 组件规范

```typescript
// 1. 使用 @property 装饰器声明响应式属性
@property({ attribute: false }) private _data: TimelineItem[] = [];

// 2. render() 方法返回 html模板
protected render(): TemplateResult {
  return html`
    <div class="container">
      ${this._data.map(item => this._renderItem(item))}
    </div>
  `;
}

// 3. 样式使用 static styles 或 css标签
static styles = css`
  .container {
    display: flex;
    flex-direction: column;
  }
`;

// 4. 事件绑定使用 @事件名
<button @click=${this._handleAddPlan}>添加</button>
<input @focusout=${this._handleFocusOut} />
```

### 模块分层

| 目录 | 职责 |
|------|------|
| `data/` | 解析 HA 实体数据 → TimelineItem |
| `services/` | 封装 HA 服务调用（save_feed, toggle, manual_feed） |
| `state/` | 缓存管理（commit/rollback）、变更检测 |
| `handlers/` | 用户交互事件处理（编辑、焦点、保存） |
| `styles/` | CSS-in-JS 样式定义 |
| `localize/` | 多语言文本 |
| `utils/` | 工具函数（时间格式化、数据转换） |

### 乐观更新模式

前端采用乐观更新策略：先修改缓存立即刷新 UI，后端 API 异步执行，失败则回滚。

```typescript
// 1. 先改缓存
weeklyCache.update(item);
// 2. 立即刷新 UI
this.requestUpdate();
// 3. 异步调用 API
try {
  await hass.callService(...);
  weeklyCache.commit();  // 成功提交
} catch {
  weeklyCache.rollback();  // 失败回滚
  this.requestUpdate();  // 恢复 UI
}
```

### 防抖与批量保存

| 场景 | 防抖时间 | 作用 |
|------|---------|------|
| 删除计划 | 5 秒 | 连续删除多个，等 5 秒后统一提交 |
| 焦点离开卡片 | 1 秒 | 编辑完成离开，等 1 秒自动保存 |
| 开关切换 | 无防抖 | 立即调用 API（乐观更新） |

### TypeScript 类型定义

```typescript
// types.ts - 核心类型定义
export interface TimelineItem {
  id: string;
  itemId: string;
  time: string;           // "HH:MM" 格式
  timeSeconds: number;    // 秒数，用于排序
  name: string;
  plannedAmount: number;
  actualAmount?: number;
  isExecuted: boolean;
  isEnabled: boolean;
  canDisable: boolean;
  canDelete: boolean;
  status: number;         // 0=正常, 1=禁用, 2=已执行
}

export interface ChangedDay {
  day: number;            // 1-7
  items: TimelineItem[];
}
```

### 编译与发布

```bash
# 开发模式（热重载）
npm run dev

# 编译生产版本
npm run build
# 输出: dist/petkit-feeder-card.js

# 发布新版本
# 1. 更新 package.json version
# 2. 创建 git tag: git tag v0.4.1
# 3. 推送: git push && git push origin v0.4.1
# GitHub Actions 自动构建
```

## 禁止事项

### 后端 (Python)
- ❌ 使用 `time.sleep()` 阻塞异步代码
- ❌ 在代码中添加 emoji 或多行注释块
- ❌ Mock 数据库或 API 进行测试（集成测试应使用真实数据）
- ❌ 省略类型注解或文档字符串
- ❌ 在实体 name 中包含设备名（使用 `has_entity_name = True`）
- ❌ 在 `async_setup_entry` 中注册服务（应在 `async_setup`）
- ❌ 服务返回非 JSON 可序列化的数据

### 前端 (TypeScript)
- ❌ 直接操作 DOM（使用 Lit 的 `render()` 和模板）
- ❌ 在 render() 中执行副作用操作
- ❌ 使用内联样式（用 `static styles` 或 CSS 类）
- ❌ 忽略类型检查（必须定义完整的 TypeScript 类型）
- ❌ 在组件外部保存状态（状态必须在组件或缓存管理器中）
- ❌ 阻塞式等待 API（使用 async/await 或 Promise）

## 参考资源

### Home Assistant 官方文档

- [Integration Development](https://developers.home-assistant.io/docs/creating_integration_index)
- [DataUpdateCoordinator](https://developers.home-assistant.io/docs/integration_fetching_data)
- [Entity Documentation](https://developers.home-assistant.io/docs/core/entity)
- [Config Flow Handler](https://developers.home-assistant.io/docs/config_entries_config_flow_handler)
- [Integration Quality Scale](https://developers.home-assistant.io/docs/core/integration-quality-scale/)
- [Lovelace Custom Cards](https://developers.home-assistant.io/docs/frontend/custom-ui/lovelace-custom-card/)

### Lit & Web Components

- [Lit 官方文档](https://lit.dev/docs/)
- [Lit 组件生命周期](https://lit.dev/docs/components/lifecycle/)
- [Lit 模板语法](https://lit.dev/docs/templates/overview/)
- [custom-card-helpers](https://github.com/custom-cards/custom-card-helpers)

### 知名集成项目参考

- [Spotify (Platinum)](https://github.com/home-assistant/core/tree/dev/homeassistant/components/spotify)
- [Bluetooth (Platinum)](https://github.com/home-assistant/core/tree/dev/homeassistant/components/bluetooth)
- [HACS (Gold)](https://github.com/hacs/integration)

### 知名 Lovelace 卡片参考

- [button-card](https://github.com/custom-cards/button-card)
- [markdown-card](https://github.com/custom-cards/markdown-card)
- [github.com/thomasloven/home-assistant-custom-ui](https://github.com/thomasloven/home-assistant-custom-ui)

## 开发流程

### 后端集成

1. **本地开发**
   - 修改 `custom_components/petkit_feeder/` 下的代码
   - 复制到 HA 配置目录测试：`cp -r custom_components/petkit_feeder ~/.homeassistant/custom_components/`
   - 或使用开发环境：`hass --config ./config`

2. **代码检查**
   ```bash
   # Lint 检查
   ruff check custom_components/petkit_feeder/
   
   # 类型检查
   mypy custom_components/petkit_feeder/
   ```

3. **提交代码**
   ```bash
   git add custom_components/petkit_feeder/
   git commit -m "feat: 新功能描述"
   git push
   ```

4. **发布版本**
   - 更新 `manifest.json` 中的 `version`
   - 推送 GitHub
   - HACS 用户可通过自定义仓库更新

### 前端卡片

1. **本地开发**
   ```bash
   cd petkit_feeder_card
   npm install
   npm run dev  # 启动热重载开发服务器
   ```

2. **编译构建**
   ```bash
   npm run build
   # 输出: dist/petkit-feeder-card.js
   ```

3. **本地测试**
   - 复制到 HA：`cp dist/petkit-feeder-card.js ~/.homeassistant/www/`
   - 在 Lovelace 中添加卡片配置测试

4. **提交与发布**
   ```bash
   # 提交源码
   git add src/
   git commit -m "fix: 修复描述"
   
   # 更新版本号（package.json）
   # 重新推送 tag 触发自动构建
   git tag -d v0.4.0
   git push origin :refs/tags/v0.4.0
   git tag v0.4.0
   git push
   git push origin v0.4.0
   ```

### 同步更新（后端 + 前端）

当同时更新后端和前端时：

```bash
# 1. 前端修改 → 编译 → 推送 tag
cd petkit_feeder_card
npm run build
git add . && git commit -m "更新卡片"
git tag -d v0.4.0 && git push origin :refs/tags/v0.4.0
git tag v0.4.0 && git push && git push origin v0.4.0

# 2. 回到主仓库，更新 submodule 引用
cd ..
git add petkit_feeder_card
git commit -m "更新前端卡片 submodule (v0.4.0)"
git push
```