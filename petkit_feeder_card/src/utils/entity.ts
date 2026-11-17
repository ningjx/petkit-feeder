/** 实体 ID 推断与查找工具 */

import { PetkitSoloCardConfig } from '../types';
import { HomeAssistant } from 'custom-card-helpers';

/**
 * 根据设备 ID 和实体类型推断实体 ID
 */
export function getEntityId(config: PetkitSoloCardConfig, entityType: string): string {
  const deviceId = config.device_id;
  if (deviceId) {
    return `sensor.petkit_feeder_${deviceId}_${entityType}`;
  }
  return config.entity || '';
}

/**
 * 获取在线状态传感器实体 ID
 */
export function getConnectivityEntityId(config: PetkitSoloCardConfig): string {
  return config.connectivity_entity || `binary_sensor.petkit_feeder_${config.device_id}_online`;
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
export function findRefreshEntity(hass: HomeAssistant, refreshEntity?: string): string | null {
  if (refreshEntity) return refreshEntity;

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