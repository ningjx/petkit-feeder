/** ============================================================================
 * 类型定义
 *
 * 分组说明：
 * - 卡片配置：用户在 YAML 中配置的选项
 * - 原始数据：从 Home Assistant 实体获取的 API 数据
 * - 处理后数据：前端组件使用的统一数据结构
 * - 变更检测：用于检测用户编辑变更的类型
 * ============================================================================ */

/** ----------------------------------------------------------------------------
 * 卡片配置
 * ---------------------------------------------------------------------------- */

/** 卡片 YAML 配置项 */
export interface PetkitSoloCardConfig {
  // 设备配置
  device_id?: string;           // 设备ID（推荐，用于自动推断 entity）

  // 实体配置（可选，如果提供 device_id 则自动推断）
  entity?: string;              // 主实体（喂食计划）
  history_entity?: string;      // 历史记录实体
  refresh_entity?: string;      // 刷新按钮实体
  feed_amount_entity?: string;  // 出粮量实体
  device_name_entity?: string;  // 设备名称实体
  connectivity_entity?: string; // 在线状态实体

  // 显示控制
  show_timeline?: boolean;     // 显示时间线（默认 true）
  show_summary?: boolean;      // 显示统计（默认 true）
  show_actions?: boolean;      // 显示操作按钮（默认 true）

  // 其他
  name?: string;               // 卡片标题（覆盖设备名称）
  history_limit?: number;      // 历史记录限制
}

/** ----------------------------------------------------------------------------
 * 原始数据（来自 Home Assistant 实体属性）
 *
 * 这些类型直接对应后端 API 返回的数据结构，
 * 在 data/parser.ts 中解析后转换为"处理后数据"
 * ---------------------------------------------------------------------------- */

/** 喂食计划项（来自 feeding_schedule 实体） */
export interface FeedingPlanItem {
  id: string;
  itemId?: string;             // 后端计划项ID，如 's21660'
  name: string;                // 计划名称
  time: string;                // HH:mm 格式
  amount: number;              // 计划克数
  enabled: boolean;            // 是否启用
  is_completed: boolean;       // 是否已完成（执行状态）
}

/** 喂食记录项（来自 feeding_records 实体） */
export interface FeedingRecord {
  id?: string;                 // 记录ID
  date: string;                // YYYY-MM-DD
  time: string;                // HH:mm
  name: string;                // 记录名称
  amount: number;              // 计划量（克）
  real_amount: number;         // 实际量（克）
  status?: number;             // 状态: 0=正常, 1=已禁用
  is_executed: boolean;        // 是否有效执行
  is_completed: boolean;       // 是否真正完成
  completed_at?: string;       // 完成时间（ISO 格式）
  src?: number;                // 来源: 1=计划喂食, 4=手动喂食
}

/** ----------------------------------------------------------------------------
 * 处理后数据（前端组件使用的统一结构）
 *
 * 这些类型在 data/merger.ts 和 data/processor.ts 中生成，
 * 将计划与记录合并为统一的时间线视图
 * ---------------------------------------------------------------------------- */

/** 时间线条目（计划与记录合并后的统一结构）
 *
 * 三种类型：
 * - plan: 正常的计划喂食项
 * - manual: 手动喂食记录
 * - deleted_plan: 已删除的计划但仍有执行记录
 */
export interface TimelineItem {
  // 基础信息
  id: string;                  // 前端生成的唯一ID
  itemId: string;              // 后端计划项ID
  time: string;                // HH:mm
  name: string;                // 显示名称
  itemType: 'plan' | 'manual' | 'deleted_plan';

  // 喂食量
  plannedAmount: number;       // 计划量（克）
  actualAmount?: number;       // 实际量（克），执行后才有

  // 状态
  isExecuted: boolean;         // 是否已执行
  isEnabled: boolean;          // 是否启用（仅 plan 有效）
  status?: number;             // 状态码: 0=正常, 1=已禁用
  completedAt?: string;        // 执行完成时间

  // 操作权限
  canDisable: boolean;         // 是否可以禁用
  canDelete: boolean;          // 是否可以删除
}

/** 今日统计数据 */
export interface TodaySummary {
  planAmount: number;          // 计划喂食总量（克）
  actualAmount: number;        // 实际喂食总量（克）
  manualAmount: number;        // 手动喂食总量（克）
  isOnline: boolean;           // 设备在线状态
  lastFeedingTime?: string;    // 最后喂食时间
  lastFeedingAmount?: number;  // 最后喂食量
  totalCount: number;          // 总喂食次数
  completedCount: number;      // 已完成次数
  pendingCount: number;        // 待执行次数
}

/** 单天数据（周视图中的某一天） */
export interface DayData {
  day: number;                 // 周几: 1-7
  weekdayName: string;         // 显示名称，通过 localize('weekday.X') 获取
  suspended: number;           // 暂停状态: 0=启用, 1=暂停
  timeline: TimelineItem[];    // 当天时间线
  summary: TodaySummary;       // 当天统计
}

/** 周视图数据（完整的一周数据） */
export interface WeeklyViewData {
  days: Map<number, DayData>;  // 按周几存储，key: 1-7
  lastUpdated: number;         // 数据更新时间戳
}

/** ----------------------------------------------------------------------------
 * 变更检测（用于检测用户编辑并提交保存）
 * ---------------------------------------------------------------------------- */

/** 编辑字段类型 */
export type EditField = 'time' | 'name' | 'amount';

/** 编辑项数据 */
export interface EditingItem {
  itemId: string;
  field: EditField;
  time: string;
  name: string;
  amount: number;
}

/** 原始项数据（用于变更对比） */
export interface OriginalItemData {
  time: string;
  name: string;
  amount: number;
}

/** 时间线差异 */
export interface TimelineDiff {
  added: TimelineItem[];
  modified: TimelineItem[];
  deleted: string[];  // itemId 列表
}

/** 有变更的周天（用于 save_feed 服务） */
export interface ChangedDay {
  day: number;                 // 周几: 1-7
  items: Array<{
    time: string;              // HH:mm
    amount: number;            // 克数
    name: string;              // 名称
    enabled: boolean;          // 是否启用
  }>;
}