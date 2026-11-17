/** 日期处理工具函数 */

/**
 * 获取今日周几数字（1-7）
 */
export function getTodayWeekdayNumber(): number {
  const day = new Date().getDay();
  return day === 0 ? 7 : day;
}