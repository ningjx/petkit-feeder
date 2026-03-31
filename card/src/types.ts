/** 卡片配置类型定义 */
export interface PetkitSoloCardConfig {
  // 设备配置
  device_id?: string;           // 设备ID（推荐，用于自动推断 entity）
  
  // 实体配置（可选，如果提供 device_id 则自动推断）
  entity?: string;              // 主实体（喂食计划）
  history_entity?: string;      // 历史记录实体
  refresh_entity?: string;      // 刷新按钮实体
  feed_amount_entity?: string;  // 出粮量实体
  device_name_entity?: string;  // 设备名称实体
  
  // 显示控制
  show_timeline?: boolean;     // 显示时间线（默认 true）
  show_summary?: boolean;      // 显示统计（默认 true）
  show_actions?: boolean;      // 显示操作按钮（默认 true）
  
  // 其他
  name?: string;               // 卡片标题（覆盖设备名称）
  history_limit?: number;      // 历史记录限制
}

/** 喂食计划项（原始数据） */
export interface FeedingPlanItem {
  id: string;
  itemId?: string;       // 后端计划项ID，如 's21660'
  name: string;
  time: string;         // HH:mm 格式
  amount: number;       // 克
  is_enabled: boolean;  // 是否启用
  is_completed: boolean; // 是否已完成
  enabled: boolean;
}

/** 喂食记录（原始数据） */
export interface FeedingRecord {
  id?: string;          // 记录ID，如 's21660'
  date: string;         // YYYY-MM-DD
  time: string;         // HH:mm
  name: string;
  amount: number;       // 计划量
  real_amount: number;  // 实际量
  status?: number;      // 状态: 0=正常, 1=已禁用
  is_executed: boolean; // 是否有效（未被删除）
  is_completed: boolean; // 是否真正执行完成
  completed_at?: string; // ISO 格式时间
  src?: number;         // 来源: 1=计划, 4=手动
}

/** 时间线条目（合并后的统一数据结构） */
export interface TimelineItem {
  // 基础信息
  id: string;                // 前端生成的唯一ID
  itemId: string;            // 后端计划项ID（通常是时间的秒数）
  time: string;              // HH:mm
  timeSeconds?: number;      // 时间秒数（用于匹配）
  name: string;              // 计划名称或"手动喂食"
  itemType: 'plan' | 'manual' | 'deleted_plan';  // 类型标识
  
  // 喂食量
  plannedAmount: number;     // 计划量（克）
  actualAmount?: number;     // 实际量（克）
  
  // 状态
  isExecuted: boolean;       // 是否已执行
  isEnabled: boolean;        // 是否启用（仅 plan 有效）
  status?: number;           // 状态: 0=正常/启用, 1=已禁用
  completedAt?: string;      // 执行完成时间（ISO 格式）
  
  // 操作权限
  canDisable: boolean;       // 可否停用（仅 plan=true）
  canDelete: boolean;        // 可否删除（仅 plan=true）
}

/** 今日统计数据 */
export interface TodaySummary {
  planAmount: number;      // 计划喂食总量（克）
  actualAmount: number;    // 实际喂食总量（克）
  manualAmount: number;    // 手动喂食总量（克）
  isOnline: boolean;       // 在线状态
  lastFeedingTime?: string; // 最后喂食时间（ISO 格式）
  lastFeedingAmount?: number; // 最后喂食量（克）
  totalCount: number;      // 总喂食次数
  completedCount: number;  // 已完成次数
  pendingCount: number;    // 待执行次数
}

/** 卡片状态 */
export interface PetkitSoloCardState {
  deviceName: string;
  isOnline: boolean;
  wifiRsq?: number;
  foodAvailable: boolean;
  timeline: TimelineItem[];
  summary: TodaySummary;
}
