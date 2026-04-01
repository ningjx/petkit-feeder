# 前端卡片重构方案

## 目标

将 `petkit-feeder-card.ts`（1610 行）拆分成多个模块，实现：
- 架构更清晰：职责分离，单一职责原则
- 模块化解耦：各模块独立，易于维护和测试
- 便于阅读：代码组织清晰，快速定位功能
- 便于调试：模块边界明确，问题定位精准
- 性能更好：减少重复代码，优化渲染逻辑

## 现状分析

### 当前文件结构

```
card/src/
├── petkit-feeder-card.ts  (1610 行) - 主组件，包含所有逻辑
├── types.ts               (96 行)  - 类型定义
└── editor.ts              (116 行) - 卡片编辑器
```

### 主组件代码分布（估算）

| 功能模块 | 行数 | 占比 |
|---------|------|------|
| 数据处理 | ~200 | 12% |
| 渲染逻辑 | ~300 | 19% |
| 样式定义 | ~500 | 31% |
| 事件处理 | ~200 | 12% |
| 服务调用 | ~100 | 6% |
| 状态管理 | ~50 | 3% |
| 工具函数 | ~50 | 3% |
| 其他 | ~210 | 13% |

### 问题

1. **单文件过大**：1610 行代码难以阅读和维护
2. **职责混杂**：数据处理、渲染、样式、事件、服务调用都在一个文件
3. **耦合度高**：各功能模块相互依赖，难以独立修改
4. **调试困难**：问题定位需要搜索整个大文件
5. **性能隐患**：样式每次重新计算，渲染逻辑未优化

## 重构方案

### 目标文件结构

```
card/src/
├── index.ts                    - 入口文件，注册组件
├── petkit-feeder-card.ts       - 主组件（精简后 ~200 行）
├── types.ts                    - 类型定义（保持不变）
├── editor.ts                   - 卡片编辑器（保持不变）
│
├── utils/                      - 工具函数
│   ├── date.ts                 - 日期处理
│   ├── entity.ts               - 实体 ID 推断
│   └── constants.ts            - 常量定义
│
├── data/                       - 数据处理模块
│   ├── parser.ts               - 数据解析（计划、记录）
│   ├── merger.ts               - 时间线合并
│   ├── summary.ts              - 统计计算
│   └── processor.ts            - 统一处理入口
│
├── styles/                     - 样式模块
│   ├── base.ts                 - 基础样式
│   ├── header.ts               - 头部样式
│   ├── timeline.ts             - 时间线样式
│   ├── button.ts               - 按钮样式
│   ├── form.ts                 - 表单样式
│   ├── summary.ts              - 统计样式
│   └── index.ts                - 样式汇总
│
├── components/                 - UI 组件
│   ├── header.ts               - 头部组件
│   ├── timeline-item.ts        - 时间线条目组件
│   ├── timeline-list.ts        - 时间线列表组件
│   ├── summary-row.ts          - 统计行组件
│   ├── action-buttons.ts       - 操作按钮组件
│   ├── add-plan-button.ts      - 新增计划按钮组件
│   ├── edit-form.ts            - 编辑表单组件
│   └── empty-state.ts          - 空状态组件
│   └── error-state.ts          - 错误状态组件
│
├── handlers/                   - 事件处理模块
│   ├── edit.ts                 - 编辑事件处理
│   ├── toggle.ts               - 开关切换处理
│   ├── delete.ts               - 删除处理
│   ├── focus.ts                - 焦点/失焦处理
│   └── save.ts                 - 保存处理
│
├── services/                   - 服务调用模块
│   ├── plan.ts                 - 计划相关服务
│   ├── device.ts               - 设备相关服务
│   └── index.ts                - 服务汇总
│
└── state/                      - 状态管理模块
    ├── edit-state.ts           - 编辑状态
    ├── pending-changes.ts      - 待提交变更
    └ manager.ts                - 状态管理器
```

### 模块职责划分

#### 1. utils/ - 工具函数

| 文件 | 职责 | 导出函数 |
|-----|------|---------|
| `date.ts` | 日期处理 | `getTodayDate()`, `getTodayWeekday()`, `formatDate()` |
| `entity.ts` | 实体 ID 推断 | `getEntityId(deviceId, entityType)` |
| `constants.ts` | 常量定义 | `TIME_TOLERANCE`, `SAVE_DELAY`, `DEFAULT_FEED_AMOUNT` |

#### 2. data/ - 数据处理模块

| 文件 | 职责 | 导出函数 |
|-----|------|---------|
| `parser.ts` | 数据解析 | `parseTodayPlans()`, `parseTodayRecords()` |
| `merger.ts` | 时间线合并 | `mergeTimeline(plans, records, pendingChanges)` |
| `summary.ts` | 统计计算 | `calculateSummary(historyAttrs, timeline)` |
| `processor.ts` | 统一入口 | `processTodayData(planAttrs, historyAttrs, pendingChanges)` |

#### 3. styles/ - 样式模块

| 文件 | 职责 | 导出内容 |
|-----|------|---------|
| `base.ts` | 基础样式 | `:host`, `ha-card` 等 |
| `header.ts` | 头部样式 | `.header`, `.header-title` 等 |
| `timeline.ts` | 时间线样式 | `.timeline-item`, `.time`, `.amount` 等 |
| `button.ts` | 按钮样式 | `.icon-btn`, `.feed-btn`, `.refresh-btn` 等 |
| `form.ts` | 表单样式 | `.edit-time`, `.edit-amount` 等 |
| `summary.ts` | 统计样式 | `.summary-row`, `.summary-item` 等 |
| `index.ts` | 样式汇总 | `combineStyles()` 合并所有样式 |

#### 4. components/ - UI 组件

| 文件 | 职责 | Props |
|-----|------|-------|
| `header.ts` | 渲染头部 | `deviceName`, `date`, `onRefresh`, `onFeed` |
| `timeline-item.ts` | 渲染时间线条目 | `item`, `editState`, `onEdit`, `onToggle`, `onDelete` |
| `timeline-list.ts` | 渲染时间线列表 | `timeline`, `editState`, `handlers` |
| `summary-row.ts` | 渲染统计行 | `summary` |
| `action-buttons.ts` | 渲染操作按钮 | `onRefresh`, `onFeed` |
| `add-plan-button.ts` | 新增计划按钮 | `onClick` |
| `edit-form.ts` | 编辑表单 | `item`, `onSave`, `onCancel` |
| `empty-state.ts` | 空状态 | 无 |
| `error-state.ts` | 错误状态 | `message` |

#### 5. handlers/ - 事件处理模块

| 文件 | 职责 | 导出函数 |
|-----|------|---------|
| `edit.ts` | 编辑处理 | `startEdit()`, `cancelEdit()` |
| `toggle.ts` | 开关切换 | `handleToggle()` |
| `delete.ts` | 删除处理 | `handleDelete()` |
| `focus.ts` | 焦点处理 | `handleFocusOut()`, `handleKeyDown()` |
| `save.ts` | 保存处理 | `saveEdit()`, `saveNewItem()` |

#### 6. services/ - 服务调用模块

| 文件 | 职责 | 导出函数 |
|-----|------|---------|
| `plan.ts` | 计划服务 | `addFeedingItem()`, `updateFeedingItem()`, `deleteFeedingItem()` |
| `device.ts` | 设备服务 | `manualFeed()`, `refreshData()` |
| `index.ts` | 服务汇总 | 导出所有服务函数 |

#### 7. state/ - 状态管理模块

| 文件 | 职责 | 导出内容 |
|-----|------|---------|
| `edit-state.ts` | 编辑状态 | `EditState` 类 |
| `pending-changes.ts` | 待提交变更 | `PendingChanges` 类 |
| `manager.ts` | 状态管理器 | `StateManager` 类，统一管理所有状态 |

### 模块依赖关系

```
                    ┌─────────────┐
                    │ petkit-     │
                    │ feeder-card │
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│ components/ │   │ handlers/   │   │ services/   │
└──────┬──────┘   └──────┬──────┘   └──────┬──────┘
       │                 │                 │
       ▼                 ▼                 ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│   styles/   │   │   state/    │   │    utils/   │
└─────────────┘   └──────┬──────┘   └─────────────┘
                         │
                         ▼
                  ┌─────────────┐
                  │    data/    │
                  └─────────────┘
```

## 执行步骤

### 阶段 1：准备工作（不改动代码）✅ 已完成

1. 创建目录结构
2. 创建空模块文件，添加注释说明职责
3. 验证构建配置支持新目录结构

### 阶段 2：提取工具函数（低风险）✅ 已完成

1. **提取 `utils/constants.ts`** ✅
   - 移入常量：`TIME_TOLERANCE = 120`, `SAVE_DELAY = 500`, `DEFAULT_FEED_AMOUNT = 10`
   - 在主组件导入并使用
   
2. **提取 `utils/date.ts`** ✅
   - 移入函数：`_getTodayDate()`, `_getTodayWeekday()`
   - 保持函数签名不变
   - 在主组件导入并使用
   
3. **提取 `utils/entity.ts`** ✅
   - 移入函数：`_getEntityId()`
   - 保持函数签名不变
   - 在主组件导入并使用
   
4. **验证测试** ✅
   - 运行构建，确认无错误
   - 功能测试，确认行为不变

### 阶段 3：提取数据处理模块（中等风险）✅ 已完成

1. **提取 `data/parser.ts`** ✅
   - 移入：`_parseTodayPlans()`, `_parseTodayRecords()`
   - 调整为纯函数，传入 weekday 参数
   
2. **提取 `data/merger.ts`** ✅
   - 移入：`_mergeTimeline()`
   - 调整为纯函数，传入 pendingChanges 参数
   
3. **提取 `data/summary.ts`** ✅
   - 移入：`_getSummaryFromAttrs()`
   - 保持为纯函数
   
4. **创建 `data/processor.ts`** ✅
   - 整合：`_processTodayData()`
   - 调用上述模块函数
   
5. **验证测试** ✅
   - 运行构建，确认无错误
   - 功能测试，确认数据处理正确

### 阶段 4：提取样式模块（低风险）✅ 已完成

1. **提取 `styles/base.ts`** ✅
   - 移入：`:host`, `ha-card` 样式
   
2. **提取 `styles/header.ts`** ✅
   - 移入：`.header`, `.header-title`, `.header-actions` 样式
   
3. **提取 `styles/timeline.ts`** ✅
   - 移入：`.timeline-item`, `.time`, `.amount`, `.name` 样式
   
4. **提取 `styles/button.ts`** ✅
   - 移入：`.icon-btn`, `.feed-btn`, `.refresh-btn` 样式
   
5. **提取 `styles/form.ts`** ✅
   - 移入：`.edit-time`, `.edit-amount`, `.edit-name` 样式
   
6. **提取 `styles/summary.ts`** ✅
   - 移入：`.summary-row`, `.summary-item` 样式
   
7. **创建 `styles/index.ts`** ✅
   - 合并所有样式：`combineStyles()`
   
8. **验证测试** ✅
   - 运行构建，确认无错误
   - 视觉测试，确认样式不变

### 阶段 5：提取状态管理模块（中等风险）✅ 已完成

1. **创建 `state/edit-state.ts`** ✅
   - 定义：`EditState` 类，管理编辑状态
   - 包含：`editingItem`, `originalItemData`, `saveTimeout`
   
2. **创建 `state/pending-changes.ts`** ✅
   - 定义：`PendingChangesManager` 类，管理待提交变更
   - 包含：`Map` 存储，增删改查方法
   
3. **创建 `state/manager.ts`** ✅
   - 定义：`StateManager` 类，统一管理
   - 组合：`EditState`, `PendingChangesManager`
   
4. **在主组件使用状态管理器**
   - 待后续集成
   
5. **验证测试**
   - 待集成后测试

### 阶段 6：提取服务调用模块（低风险）⏳ 待执行

1. **提取 `services/plan.ts`**
   - 移入：`_updatePlan()`, `_saveNewItem()`, `_disablePlan()`, `_deletePlan()`
   - 调整为函数，传入 `hass`, `config` 参数
   
2. **提取 `services/device.ts`**
   - 移入：手动喂食、刷新数据服务调用
   
3. **创建 `services/index.ts`**
   - 导出所有服务函数
   
4. **验证测试**
   - 运行构建，确认无错误
   - 服务调用测试，确认功能不变

### 阶段 7：提取事件处理模块（中等风险）

1. **提取 `handlers/edit.ts`**
   - 移入：`_startEdit()`, `_cancelEdit()`
   - 使用 `StateManager` 管理状态
   
2. **提取 `handlers/toggle.ts`**
   - 移入：`_handleToggle()`
   
3. **提取 `handlers/delete.ts`**
   - 移入：`_handleDelete()`
   
4. **提取 `handlers/focus.ts`**
   - 移入：`_handleFocusOut()`, `_handleKeyDown()`
   
5. **提取 `handlers/save.ts`**
   - 移入：保存逻辑，调用 services
   
6. **验证测试**
   - 运行构建，确认无错误
   - 交互测试，确认事件处理正确

### 阶段 8：提取 UI 组件模块（高风险）

1. **提取 `components/empty-state.ts`**
   - 移入：空状态渲染
   
2. **提取 `components/error-state.ts`**
   - 移入：错误状态渲染
   
3. **提取 `components/add-plan-button.ts`**
   - 移入：新增计划按钮渲染
   
4. **提取 `components/summary-row.ts`**
   - 移入：统计行渲染
   
5. **提取 `components/header.ts`**
   - 移入：头部渲染
   
6. **提取 `components/timeline-item.ts`**
   - 移入：时间线条目渲染（最复杂）
   - 分步：先提取静态渲染，再提取编辑状态
   
7. **提取 `components/timeline-list.ts`**
   - 移入：时间线列表渲染
   
8. **验证测试**
   - 每提取一个组件后测试
   - 视觉测试，确认渲染正确

### 阘段 9：整合与优化

1. **精简主组件 `petkit-feeder-card.ts`**
   - 只保留：属性定义、配置处理、组合各模块
   - 目标：~200 行
   
2. **创建 `index.ts` 入口文件**
   - 注册组件到 `customCards`
   
3. **优化导入**
   - 检查循环依赖
   - 简化导入路径
   
4. **性能优化**
   - 使用 `memoize` 缓存数据处理结果
   - 优化样式计算
   
5. **最终验证**
   - 全面功能测试
   - 性能测试
   - 代码审查

## 风险评估

| 阶段 | 风险 | 原因 | 缓解措施 |
|-----|------|------|---------|
| 阶段 1 | 低 | 不改动代码 | 无需测试 |
| 阶段 2 | 低 | 工具函数独立 | 独立函数，易于验证 |
| 阶段 3 | 中 | 数据处理有依赖 | 保持函数签名，逐步提取 |
| 阶段 4 | 低 | 样式独立 | CSS 可独立验证 |
| 阶段 5 | 中 | 状态管理影响交互 | 使用类封装，保持接口 |
| 阶段 6 | 低 | 服务调用独立 | 函数封装，易于测试 |
| 阶段 7 | 中 | 事件处理有依赖 | 使用 StateManager |
| 阶段 8 | 高 | 组件渲染最复杂 | 分步提取，每步测试 |
| 阘段 9 | 低 | 整合优化 | 全面测试 |

## 性能优化计划

### 1. 数据处理缓存

```typescript
// 使用 memoize 缓存数据处理结果
import { memoize } from 'lit/decorators/memoize.js';

class PetkitFeederCard extends LitElement {
  @memoize()
  private _processData(planAttrs: any, historyAttrs: any) {
    return processTodayData(planAttrs, historyAttrs, this._state.pendingChanges);
  }
}
```

### 2. 渲染优化

- 使用 `repeat` 指令优化列表渲染
- 使用 `cache` 指令缓存 DOM

### 3. 样式优化

- 将样式计算移到模块，避免每次渲染重新计算
- 使用 CSS 变量统一管理主题色

## 验收标准

1. **架构清晰度**
   - 主组件行数 < 300
   - 模块职责单一，无交叉
   - 依赖关系清晰，无循环

2. **可读性**
   - 每个文件 < 200 行
   - 函数命名清晰，职责明确
   - 注释完整，易于理解

3. **可调试性**
   - 模块边界明确
   - 日志按模块输出
   - 错误定位精准

4. **性能**
   - 首次渲染时间 < 100ms
   - 数据更新响应 < 50ms
   - 内存占用优化

5. **功能完整性**
   - 所有原有功能保持不变
   - 所有交互行为保持不变
   - 所有样式保持不变

## 时间估算

| 阶段 | 工时 | 备注 |
|-----|------|------|
| 阶段 1 | 0.5h | 创建目录 |
| 阶段 2 | 1h | 提取工具函数 |
| 阶段 3 | 2h | 提取数据处理 |
| 阶段 4 | 1h | 提取样式 |
| 阶段 5 | 2h | 提取状态管理 |
| 阶段 6 | 1h | 提取服务调用 |
| 阶段 7 | 2h | 提取事件处理 |
| 阶段 8 | 4h | 提取 UI 组件 |
| 阶段 9 | 2h | 整合优化 |
| **总计** | **15.5h** | |

## 备注

- 所有提取操作保持函数签名不变，确保兼容性
- 每个阶段完成后提交代码，便于回滚
- 高风险阶段（阶段 8）需要充分测试
- 可根据实际情况调整执行顺序和模块划分