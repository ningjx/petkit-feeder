/** 周数据缓存管理 */

import { WeeklyViewData, DayData, TimelineItem, ChangedDay } from '../types';
import { detectDayChanges } from './diff-detector';

/**
 * 周数据缓存管理类
 * 维护原始数据和编辑缓存，支持差异检测和回滚
 */
export class WeeklyCacheManager {
  private _originData: WeeklyViewData | null = null;
  private _cacheData: WeeklyViewData | null = null;

  /** 获取原始数据 */
  get originData(): WeeklyViewData | null {
    return this._originData;
  }

  /** 初始化原始数据 */
  initOrigin(data: WeeklyViewData): void {
    this._originData = this._deepClone(data);
    this._cacheData = this._deepClone(data);
  }

  /** 获取某天的缓存数据 */
  getDayCache(day: number): DayData | null {
    return this._cacheData?.days.get(day) || null;
  }

  /** 回滚到原始数据 */
  rollback(): void {
    if (this._originData) {
      this._cacheData = this._deepClone(this._originData);
    }
  }

  /** 提交更改（用缓存覆盖原始数据） */
  commit(): void {
    if (this._cacheData) {
      this._originData = this._deepClone(this._cacheData);
    }
  }

  /** 检测所有有差异的周天 */
  detectChanges(): ChangedDay[] {
    if (!this._originData || !this._cacheData) {
      return [];
    }

    const changedDays: ChangedDay[] = [];

    for (let day = 1; day <= 7; day++) {
      const originDay = this._originData.days.get(day);
      const cacheDay = this._cacheData.days.get(day);

      if (!originDay || !cacheDay) continue;

      const changes = detectDayChanges(originDay.timeline, cacheDay.timeline);
      if (changes) {
        changedDays.push({
          day,
          items: cacheDay.timeline
            .filter(item => item.itemType === 'plan')
            .map(item => ({
              time: item.time,
              amount: item.plannedAmount,
              name: item.name,
              enabled: item.isEnabled,
            })),
        });
      }
    }

    return changedDays;
  }

  /** 深克隆周数据 */
  private _deepClone(data: WeeklyViewData): WeeklyViewData {
    const days = new Map<number, DayData>();
    data.days.forEach((dayData, day) => {
      days.set(day, {
        ...dayData,
        timeline: this._deepCloneTimeline(dayData.timeline),
        summary: { ...dayData.summary },
      });
    });
    return {
      days,
      lastUpdated: data.lastUpdated,
    };
  }

  /** 深克隆时间线 */
  private _deepCloneTimeline(timeline: TimelineItem[]): TimelineItem[] {
    return timeline.map(item => ({ ...item }));
  }
}