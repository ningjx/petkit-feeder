/** 设备相关服务 */

import { HomeAssistant } from 'custom-card-helpers';

/**
 * 手动喂食
 */
export async function manualFeed(
  hass: HomeAssistant,
  onError?: (error: any) => void
): Promise<void> {
  const feedEntity = findManualFeedEntity(hass);

  if (feedEntity) {
    try {
      await hass.callService('button', 'press', {
        entity_id: feedEntity
      });
    } catch (error) {
      console.error('[PetkitFeeder] 手动喂食失败:', error);
      onError?.(error);
    }
  }
}

/**
 * 刷新数据
 */
export async function refreshData(
  hass: HomeAssistant,
  refreshEntity?: string,
  onError?: (error: any) => void
): Promise<void> {
  const entity = refreshEntity || findRefreshEntity(hass);

  if (entity) {
    try {
      await hass.callService('button', 'press', {
        entity_id: entity
      });
    } catch (error) {
      console.error('[PetkitFeeder] 刷新失败:', error);
      onError?.(error);
    }
  }
}

/**
 * 查找手动喂食按钮实体
 */
export function findManualFeedEntity(hass: HomeAssistant): string | null {
  for (const entityId in hass.states) {
    if (entityId.startsWith('button.') && entityId.includes('petkit')) {
      const state = hass.states[entityId];
      const friendlyName = state?.attributes?.friendly_name || '';
      if (friendlyName.includes('手动') || friendlyName.includes('出粮') ||
          friendlyName.toLowerCase().includes('feed')) {
        if (!friendlyName.includes('刷新') && !friendlyName.toLowerCase().includes('refresh')) {
          return entityId;
        }
      }
    }
  }
  return null;
}

/**
 * 查找刷新按钮实体
 */
export function findRefreshEntity(hass: HomeAssistant): string | null {
  for (const entityId in hass.states) {
    if (entityId.startsWith('button.') && entityId.includes('petkit')) {
      const state = hass.states[entityId];
      const friendlyName = state?.attributes?.friendly_name || '';
      if (friendlyName.includes('刷新') || friendlyName.toLowerCase().includes('refresh')) {
        return entityId;
      }
    }
  }
  return null;
}