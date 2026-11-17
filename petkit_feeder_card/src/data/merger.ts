/** 时间线合并模块 */

import { FeedingPlanItem, FeedingRecord, TimelineItem } from '../types';

/**
 * 合并计划与记录，生成时间线
 */
export function mergeTimeline(
  plans: FeedingPlanItem[],
  records: FeedingRecord[]
): TimelineItem[] {
  const planItems: TimelineItem[] = plans.map((plan, index) => {
    return {
      id: `plan_${plan.itemId || plan.time}_${index}`,
      itemId: plan.itemId || plan.time,
      time: plan.time,
      name: plan.name,
      itemType: 'plan' as const,
      plannedAmount: plan.amount,
      isExecuted: false,
      isEnabled: plan.enabled,
      canDisable: true,
      canDelete: true,
    };
  });

  const recordItems: (TimelineItem | null)[] = records.map((record, index) => {
    let matchedPlan: TimelineItem | undefined;

    if (record.src === 1) {
      matchedPlan = planItems.find(p => {
        return p.time === record.time && p.plannedAmount === record.amount;
      });
    }

    if (matchedPlan) {
      matchedPlan.isExecuted = record.is_completed;
      matchedPlan.actualAmount = record.real_amount;
      matchedPlan.completedAt = record.completed_at;
      matchedPlan.isEnabled = record.status === 0;
      matchedPlan.status = record.status;
      return null;
    }

    if (record.src === 1) {
      return {
        id: `deleted_plan_${record.id || record.time}_${index}`,
        itemId: record.id || record.time,
        time: record.time,
        name: record.name || '已删除计划',
        itemType: 'deleted_plan' as const,
        plannedAmount: record.amount,
        actualAmount: record.real_amount,
        isExecuted: record.is_completed,
        isEnabled: false,
        completedAt: record.completed_at,
        canDisable: false,
        canDelete: false,
      } as TimelineItem;
    }

    return {
      id: `manual_${record.id || record.time}_${index}`,
      itemId: record.id || record.time,
      time: record.time,
      name: record.name || '手动喂食',
      itemType: 'manual' as const,
      plannedAmount: 0,
      actualAmount: record.real_amount,
      isExecuted: record.is_completed,
      isEnabled: true,
      completedAt: record.completed_at,
      canDisable: false,
      canDelete: false,
    } as TimelineItem;
  });

  const validItems = recordItems.filter((item): item is TimelineItem => item !== null);
  return [...planItems, ...validItems]
    .sort((a, b) => a.time.localeCompare(b.time));
}