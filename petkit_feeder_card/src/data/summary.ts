/** 统计计算模块 */

import { TimelineItem, TodaySummary } from '../types';

/** 获取空的统计对象 */
export function getEmptySummary(): TodaySummary {
  return {
    planAmount: 0,
    actualAmount: 0,
    manualAmount: 0,
    isOnline: false,
    totalCount: 0,
    completedCount: 0,
    pendingCount: 0,
  };
}

/**
 * 从喂食记录传感器中读取指定日期的统计数据
 * @param historyAttrs 喂食历史实体属性
 * @param dateStr 日期字符串 (YYYY-MM-DD)
 * @param timeline 时间线数据
 * @param isOnline 在线状态
 * @returns 统计数据
 */
export function calculateSummary(
  historyAttrs: any,
  dateStr: string,
  timeline: TimelineItem[],
  isOnline: boolean
): TodaySummary {
  // 从喂食记录传感器读取对应日期的数据
  const records = historyAttrs.records || {};
  const dayData = records[dateStr] || {};
  
  const planAmount = dayData.plan_amount || 0;
  const actualAmount = dayData.real_amount || 0;
  const manualAmount = dayData.add_amount || 0;
  
  const totalCount = dayData.times || timeline.length;
  const completedCount = timeline.filter(item => item.isExecuted).length;
  const pendingCount = totalCount - completedCount;

  const executedItems = timeline.filter(item => item.isExecuted && item.completedAt);
  const lastFeedingItem = executedItems.length > 0
    ? executedItems.reduce((latest, current) =>
        current.completedAt! > latest.completedAt! ? current : latest
      )
    : undefined;

  return {
    planAmount,
    actualAmount,
    manualAmount,
    isOnline,
    lastFeedingTime: lastFeedingItem?.completedAt,
    lastFeedingAmount: lastFeedingItem?.actualAmount,
    totalCount,
    completedCount,
    pendingCount,
  };
}