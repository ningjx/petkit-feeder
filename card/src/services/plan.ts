/** 计划相关服务 */

import { HomeAssistant } from 'custom-card-helpers';
import { TimelineItem } from '../types';
import { PendingChange } from '../../data';
import { getTodayWeekdayNumber } from '../../utils';

/**
 * 切换计划启用状态
 */
export async function toggleFeedingItem(
  hass: HomeAssistant,
  item: TimelineItem,
  pendingChanges: Map<string, PendingChange>,
  onSuccess?: () => void,
  onError?: (error: any) => void
): Promise<void> {
  if (item.isExecuted) return;

  const newEnabled = !item.isEnabled;
  if (item.isEnabled === newEnabled) return;

  const weekday = getTodayWeekdayNumber();

  // 乐观更新
  pendingChanges.set(item.itemId, {
    time: item.time,
    name: item.name,
    amount: item.plannedAmount,
    enabled: newEnabled,
  });
  onSuccess?.();

  try {
    await hass.callService('petkit_feeder', 'toggle_feeding_item', {
      day: weekday,
      item_id: item.itemId,
      enabled: newEnabled
    });
    pendingChanges.delete(item.itemId);
  } catch (error) {
    pendingChanges.delete(item.itemId);
    onError?.(error);
    console.error('[PetkitFeeder] 切换失败:', error);
    alert(`切换失败: ${error}`);
  }
}

/**
 * 删除计划
 */
export async function deleteFeedingItem(
  hass: HomeAssistant,
  item: TimelineItem,
  pendingChanges: Map<string, PendingChange>,
  onSuccess?: () => void,
  onError?: (error: any) => void
): Promise<void> {
  const weekday = getTodayWeekdayNumber();

  console.log('[PetkitFeeder] 删除计划:', {
    day: weekday,
    item_id: item.itemId,
    item_name: item.name,
    item_time: item.time
  });

  // 乐观更新
  pendingChanges.set(item.itemId, {
    time: item.time,
    name: item.name,
    amount: item.plannedAmount,
    deleted: true,
  });
  onSuccess?.();

  try {
    await hass.callService('petkit_feeder', 'remove_feeding_item', {
      day: weekday,
      item_id: item.itemId
    });
    console.log('[PetkitFeeder] 删除计划成功');
  } catch (error) {
    console.error('[PetkitFeeder] 删除计划失败:', error);
    pendingChanges.delete(item.itemId);
    onError?.();
  }
}

/**
 * 更新计划
 */
export async function updateFeedingItem(
  hass: HomeAssistant,
  editData: { itemId: string; time: string; name: string; amount: number },
  pendingChanges: Map<string, PendingChange>,
  onSuccess?: () => void,
  onError?: (error: any) => void
): Promise<void> {
  const weekday = getTodayWeekdayNumber();

  console.log('[PetkitFeeder] 更新计划:', {
    day: weekday,
    item_id: editData.itemId,
    time: editData.time,
    amount: editData.amount,
    name: editData.name,
  });

  try {
    await hass.callService('petkit_feeder', 'update_feeding_item', {
      day: weekday,
      item_id: editData.itemId,
      time: editData.time,
      amount: editData.amount,
      name: editData.name,
    });
    console.log('[PetkitFeeder] 更新计划成功');
    pendingChanges.delete(editData.itemId);
    onSuccess?.();
  } catch (error) {
    console.error('[PetkitFeeder] 更新计划失败:', error);
    pendingChanges.delete(editData.itemId);
    onError?.(error);
  }
}

/**
 * 新增计划
 */
export async function addFeedingItem(
  hass: HomeAssistant,
  editData: { itemId: string; time: string; name: string; amount: number },
  pendingChanges: Map<string, PendingChange>,
  existingTimes?: string[],
  onSuccess?: () => void,
  onError?: (error: any) => void
): Promise<void> {
  // 检查时间点是否已存在
  if (existingTimes && existingTimes.includes(editData.time)) {
    console.log('[PetkitFeeder] 该时间点已存在计划，跳过保存');
    pendingChanges.delete(editData.itemId);
    onSuccess?.();
    return;
  }

  const weekday = getTodayWeekdayNumber();

  console.log('[PetkitFeeder] 保存新计划:', {
    day: weekday,
    time: editData.time,
    amount: editData.amount,
    name: editData.name,
  });

  try {
    await hass.callService('petkit_feeder', 'add_feeding_item', {
      day: weekday,
      time: editData.time,
      amount: editData.amount,
      name: editData.name,
    });
    console.log('[PetkitFeeder] 保存新计划成功');
    pendingChanges.delete(editData.itemId);
    onSuccess?.();
  } catch (error) {
    console.error('[PetkitFeeder] 保存新计划失败:', error);
    onError?.(error);
  }
}