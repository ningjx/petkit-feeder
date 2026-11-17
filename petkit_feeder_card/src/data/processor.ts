/** 数据处理统一入口 */

import { WeeklyViewData, DayData } from '../types';
import { parseWeeklyPlans, parseDayRecords, getWeekDates } from './parser';
import { mergeTimeline } from './merger';
import { calculateSummary } from './summary';
import { localize } from '../localize';

/**
 * 处理一周数据
 * @param planAttrs 喂食计划实体属性
 * @param historyAttrs 喂食记录实体属性
 * @param isOnline 设备在线状态
 * @param language 语言代码 ('zh' | 'en')
 */
export function processWeeklyData(
  planAttrs: any,
  historyAttrs: any,
  isOnline: boolean,
  language: string = 'zh'
): WeeklyViewData {
  const weeklyPlans = parseWeeklyPlans(planAttrs);
  const weekDates = getWeekDates();
  const days = new Map<number, DayData>();

  for (let day = 1; day <= 7; day++) {
    const planData = weeklyPlans.get(day) || { suspended: 0, items: [] };
    const dateStr = weekDates[day - 1];
    const records = parseDayRecords(historyAttrs, dateStr);

    const timeline = mergeTimeline(planData.items, records);
    const summary = calculateSummary(historyAttrs, dateStr, timeline, isOnline);

    days.set(day, {
      day,
      weekdayName: localize(`weekday.${day}`, language),
      suspended: planData.suspended,
      timeline,
      summary,
    });
  }

  return {
    days,
    lastUpdated: Date.now(),
  };
}