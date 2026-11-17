/** Home Assistant 基础服务调用 */

import { HomeAssistant } from 'custom-card-helpers';

/**
 * 按下按钮实体
 * @param hass Home Assistant 实例
 * @param entityId 按钮实体ID
 * @param logName 日志名称（用于错误提示）
 */
export async function pressButton(
  hass: HomeAssistant,
  entityId: string,
  logName: string = 'Button'
): Promise<void> {
  try {
    await hass.callService('button', 'press', { entity_id: entityId });
  } catch (error) {
    console.error(`[PetkitFeeder] ${logName}失败:`, error);
  }
}