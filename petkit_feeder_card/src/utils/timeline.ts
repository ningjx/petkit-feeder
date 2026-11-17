/** 时间线相关工具函数 */

import { TimelineItem } from '../types';
import { getTodayWeekdayNumber } from './date';

/**
 * 判断计划项是否已过期
 * @param item 时间线条目
 * @param selectedDay 当前选中的周几 (1-7)
 */
export function isItemExpired(item: TimelineItem, selectedDay: number): boolean {
  const today = getTodayWeekdayNumber();
  const isToday = selectedDay === today;
  const isPast = selectedDay < today;

  if (isPast) return true;
  if (!isToday || !item.time) return false;

  const now = new Date();
  const currentMinutes = now.getHours() * 60 + now.getMinutes();
  const [hours, minutes] = item.time.split(':').map(Number);
  return hours * 60 + minutes < currentMinutes;
}

/**
 * 获取开关提示文本
 * @param item 时间线条目
 * @param isExpired 是否过期
 * @param localizeFn 本地化函数
 */
export function getToggleTitle(
  item: TimelineItem,
  isExpired: boolean,
  localizeFn: (key: string) => string
): string {
  if (item.itemType === 'deleted_plan') {
    return localizeFn('status.deleted');
  }
  if (isExpired) {
    return localizeFn('status.expired');
  }
  if (item.isExecuted) {
    return localizeFn('status.executed');
  }
  return item.isEnabled
    ? localizeFn('status.click_disable')
    : localizeFn('status.click_enable');
}

/**
 * 获取日期显示文本
 * @param selectedDay 当前选中的周几 (1-7)
 * @param localizeFn 本地化函数
 */
export function getDateDisplay(
  selectedDay: number,
  localizeFn: (key: string, params?: Record<string, string | number>) => string
): string {
  const today = new Date();
  const currentWeekday = today.getDay();
  const currentWeekdayNum = currentWeekday === 0 ? 7 : currentWeekday;

  const daysDiff = selectedDay - currentWeekdayNum;
  const targetDate = new Date(today);
  targetDate.setDate(today.getDate() + daysDiff);

  const month = targetDate.getMonth() + 1;
  const day = targetDate.getDate();
  const weekday = localizeFn(`weekday.${selectedDay}`);
  return localizeFn('date.format', { month, day, weekday });
}