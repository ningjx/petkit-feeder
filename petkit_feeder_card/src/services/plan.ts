/** 计划相关服务 */

import { HomeAssistant } from 'custom-card-helpers';
import { TimelineItem, ChangedDay } from '../types';
import { WeeklyCacheManager } from '../state';

/** 服务调用结果 */
export interface ServiceResult {
  success: boolean;
  error?: any;
}

/**
 * 批量保存喂食计划
 * @param hass Home Assistant 实例
 * @param changedDays 有变更的周天列表
 * @param weeklyCache 缓存管理器
 * @returns 服务调用结果
 */
export async function saveFeed(
  hass: HomeAssistant,
  changedDays: ChangedDay[],
  weeklyCache: WeeklyCacheManager
): Promise<ServiceResult> {
  if (changedDays.length === 0) {
    console.log('[PetkitFeeder] 无变更，跳过保存');
    return { success: true };
  }

  console.log('[PetkitFeeder] 批量保存计划:', changedDays);

  try {
    await hass.callService('petkit_feeder', 'save_feed', {
      weekly_plan: changedDays.map(day => ({
        day: day.day,
        suspended: 0,
        items: day.items,
      })),
    });

    console.log('[PetkitFeeder] 批量保存计划成功');
    weeklyCache.commit();
    return { success: true };
  } catch (error) {
    console.error('[PetkitFeeder] 批量保存计划失败:', error);
    weeklyCache.rollback();
    return { success: false, error };
  }
}

/**
 * 切换计划启用状态（乐观更新）
 * @param hass Home Assistant 实例
 * @param day 周几 (1-7)
 * @param item 时间线条目
 * @param weeklyCache 缓存管理器
 * @returns 服务调用结果
 */
export async function toggleFeedingItem(
  hass: HomeAssistant,
  day: number,
  item: TimelineItem,
  weeklyCache: WeeklyCacheManager
): Promise<ServiceResult> {
  if (item.isExecuted) {
    return { success: false, error: 'Item already executed' };
  }

  const newEnabled = !item.isEnabled;

  // 乐观更新：先修改缓存
  const dayCache = weeklyCache.getDayCache(day);
  if (dayCache) {
    const timelineItem = dayCache.timeline.find(t => t.itemId === item.itemId);
    if (timelineItem) {
      timelineItem.isEnabled = newEnabled;
      timelineItem.status = newEnabled ? 0 : 1;
    }
  }

  try {
    await hass.callService('petkit_feeder', 'toggle_feeding_item', {
      day: day,
      item_id: item.itemId,
      enabled: newEnabled,
    });
    console.log('[PetkitFeeder] 切换状态成功');
    weeklyCache.commit();
    return { success: true };
  } catch (error) {
    console.error('[PetkitFeeder] 切换状态失败:', error);
    weeklyCache.rollback();
    return { success: false, error };
  }
}