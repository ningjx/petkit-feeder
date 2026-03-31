/** 小佩 SOLO 喂食器卡片 - 主组件（时间线版本） */

import { LitElement, html, css, svg } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import { ref } from 'lit/directives/ref.js';
import { HomeAssistant } from 'custom-card-helpers';
import { PetkitSoloCardConfig, TimelineItem, TodaySummary, FeedingPlanItem, FeedingRecord } from './types';

// 注册到卡片选择器
(window as any).customCards = (window as any).customCards || [];
(window as any).customCards.push({
  type: 'petkit-solo-card',
  name: '小佩 SOLO 喂食器',
  description: '显示小佩 SOLO 喂食器状态、喂食计划和历史记录',
  preview: true,
  documentationURL: 'https://github.com/yourusername/petkit-ha',
});

@customElement('petkit-solo-card')
export class PetkitSoloCard extends LitElement {
  @property({ attribute: false }) public hass!: HomeAssistant;
  @property({ attribute: false }) private _config?: PetkitSoloCardConfig;
  private _pendingPlanChanges: Map<string, { time: string; name: string; amount: number; enabled?: boolean; deleted?: boolean }> = new Map();
  private _editingItem: { itemId: string; field: 'time' | 'name' | 'amount'; time: string; name: string; amount: number } | null = null;
  private _originalItemData: { time: string; name: string; amount: number } | null = null;
  private _pendingNewItem: { itemId: string; time: string; name: string; amount: number } | null = null;
  private _saveTimeout: number | null = null;

  static getStubConfig(): PetkitSoloCardConfig {
    return {
      entity: 'sensor.petkit_solo_feeding_schedule',
      history_entity: 'sensor.petkit_solo_feeding_history',
      name: '小佩 SOLO 喂食器',
      show_timeline: true,
      show_summary: true,
      show_actions: true,
    };
  }

  static getConfigElement() {
    return document.createElement('petkit-solo-card-editor');
  }

  public setConfig(config: PetkitSoloCardConfig): void {
    if (!config.entity) {
      throw new Error('需要定义 entity');
    }
    this._config = {
      ...config,
      show_timeline: config.show_timeline ?? true,
      show_summary: config.show_summary ?? true,
      show_actions: config.show_actions ?? true,
    };
  }

  protected shouldUpdate(): boolean {
    return true;
  }

  protected render() {
    if (!this._config || !this.hass) {
      return html`<div>加载中...</div>`;
    }

    // 获取实体数据
    const planEntity = this.hass.states[this._config.plan_entity || this._config.entity];
    const historyEntity = this._config.history_entity 
      ? this.hass.states[this._config.history_entity] 
      : null;

    if (!planEntity) {
      return html`
        <ha-card>
          <div class="error-state">
            <ha-icon .icon=${'mdi:alert-circle'}></ha-icon>
            <p>实体不存在：${this._config.entity}</p>
          </div>
        </ha-card>
      `;
    }

    // 处理数据
    const { timeline, summary } = this._processTodayData(
      planEntity.attributes,
      historyEntity?.attributes || {}
    );

    const deviceName = this._config.name || planEntity.attributes.friendly_name || '小佩 SOLO 喂食器';

return html`
      <ha-card @focusout=${this._handleCardFocusOut}>
        <div class="header">
          <span class="header-title">${deviceName}</span>
          <span class="header-date">${this._getDateDisplay()}</span>
          <div class="header-actions">
            <button 
              class="icon-btn refresh-btn" 
              @click=${this._handleRefresh}
              title="刷新数据"
            >
              <svg viewBox="0 0 1024 1024" class="btn-svg">
                <path d="M680.64 32.768a41.6 41.6 0 0 0-56.384-17.152c-10.88 5.824-16 15.808-20.864 27.072l-22.336 47.68A450.752 450.752 0 0 0 512 85.12C271.68 85.12 74.688 275.072 74.688 512c0 77.952 21.44 151.04 58.816 213.952a41.6 41.6 0 0 0 57.088 14.528 41.856 41.856 0 0 0 14.464-57.28A333.696 333.696 0 0 1 157.952 512c0-188.48 157.312-343.36 354.048-343.36 36.288 0 71.232 5.248 104.064 15.04l1.984 0.64c16.64 4.928 32.064 9.536 44.032 11.776 6.144 1.216 14.592 2.432 23.36 1.664a50.56 50.56 0 0 0 35.2-17.92 50.688 50.688 0 0 0 10.944-37.312 81.472 81.472 0 0 0-5.888-22.656 442.944 442.944 0 0 0-19.2-38.528l-0.96-1.92-24.96-46.72zM890.56 298.048a41.6 41.6 0 0 0-57.152-14.528 41.856 41.856 0 0 0-14.464 57.28c30.016 50.432 47.104 108.8 47.104 171.2 0 188.48-157.312 343.36-354.048 343.36a363.968 363.968 0 0 1-104.064-15.04l-2.176-0.64a504 504 0 0 0-43.84-11.776 85.952 85.952 0 0 0-23.36-1.664 50.56 50.56 0 0 0-35.2 17.92 50.752 50.752 0 0 0-10.944 37.312c0.832 8.96 3.648 16.96 5.888 22.656 4.416 10.88 11.584 24.32 19.136 38.464l25.92 48.64a41.6 41.6 0 0 0 56.384 17.152c10.88-5.824 16.384-17.152 20.864-27.072L448 934.4c20.928 2.944 42.24 4.48 64 4.48 240.32 0 437.312-189.888 437.312-426.88 0-77.952-21.44-151.04-58.752-213.952z"/>
              </svg>
            </button>
            <button 
              class="icon-btn feed-btn" 
              @click=${this._handleManualFeed}
              title="手动喂食"
            >
              <svg viewBox="150 150 724 724" class="btn-svg">
                <path d="M431.424 246.336c36.576-14.208 74.112-1.024 107.04 40.48l-0.32-0.384-2.016-2.464 7.264-3.84c42.432-21.44 83.84-22.304 112 16.128l0.864 1.248 3.552-1.92c34.24-17.376 75.168-2.144 116.832 50.304l5.024 6.496 3.2 4.416c4.16 6.848 6.4 14.4 6.4 22.272l-0.128-2.752 1.76 13.76 2.56 17.664c0.96 6.176 1.984 12.608 3.104 19.328 6.4 38.24 14.368 76.448 24 111.968 9.216 34.08 19.52 63.808 30.24 86.816l2.72 5.76 1.504 3.744c1.6 4.224 2.848 8.448 3.616 12.736 0.608 3.104 0.928 6.176 0.928 9.248 0 69.312-162.336 126.272-343.552 128.352l-10.272 0.064c-186.88 0-353.888-55.232-353.888-125.536 0-7.136 1.408-14.112 3.904-21.76 1.216-3.68 2.56-7.136 4.48-11.936l3.648-9.056c0.736-1.92 1.12-3.2 1.792-5.44a786.496 786.496 0 0 0 43.648-166.016c2.72-18.432 4.448-35.104 5.408-49.664l0.672-13.44 0.096-3.84 0.32-5.184a43.52 43.52 0 0 1 7.264-18.912l2.272-3.488c4.96-8.32 13.568-19.904 25.696-31.552 34.496-33.12 76.672-45.216 121.152-20.16l-2.464-1.312 2.336-3.328c14.4-20.224 31.04-36.48 50.688-45.92z m318.912 183.04c-49.728 25.664-140.224 39.104-245.952 39.104h-10.24c-99.072-0.864-183.712-13.696-232.416-37.44a821.888 821.888 0 0 1-48.48 196l-1.664 5.408a161.76 161.76 0 0 1-2.24 5.696l-2.656 6.528c-1.568 3.84-2.528 6.4-3.296 8.736a25.408 25.408 0 0 0-1.504 6.816c0 29.44 145.504 77.536 305.856 77.536 155.968 0 299.712-48.192 305.6-78.496l0.192-2.016-0.064-0.384a28.256 28.256 0 0 0-1.376-4.512l-1.088-2.688-1.184-2.432c-12.576-26.88-23.68-59.104-33.6-95.648a1218.656 1218.656 0 0 1-25.024-116.608z m-416.096 85.12a24 24 0 0 1 24.16 20.288l0.32 3.648c0.256 28.576-6.496 71.712-26.88 121.92a24 24 0 1 1-44.48-18.08c10.336-25.44 16.96-50.08 20.544-73.056 0.832-5.44 1.472-10.496 1.92-15.168l0.736-9.504 0.128-5.632a24 24 0 0 1 23.552-24.384z m166.624-197.824c-20.64-26.048-36.544-31.616-52.064-25.6-13.44 5.216-27.392 19.2-39.36 37.344-12.832 19.488-38.784 24.48-58.816 13.152l-4.544-2.336c-21.12-9.696-40.384-3.296-59.744 15.264l-3.072 3.072-1.696 1.856-1.152 1.344 2.464 1.312c39.488 19.232 80.736 4.48 112.384-30.08l5.12-5.952 2.688-2.88c11.072-11.136 20.992-17.92 29.888-20.288 8.128-2.176 15.552-0.32 24.96 8.96l2.912 3.008 3.072 3.392c25.344 28.8 48.96 43.264 87.936 28.608l4.352-1.792 4.416-1.92c39.264-17.664 72.448-12.352 103.136 32.64l2.56 3.776c27.328 40.96 38.144 102.656 34.944 177.984l-0.448 9.6-0.384 6.464-0.256 5.632a24 24 0 0 1-47.936-2.048l0.064-1.664 0.384-7.552 0.32-7.552c2.24-56.128-5.44-101.44-22.912-131.2l-1.536-2.368c-14.08-20.544-27.136-25.536-45.824-18.752l-2.688 1.024-4.352 1.792c-54.912 21.504-97.28 3.328-134.08-36.8z"/>
              </svg>
            </button>
          </div>
        </div>

        ${this._config.show_timeline ? this._renderTimeline(timeline) : ''}
        ${this._config.show_timeline ? this._renderAddPlanButton() : ''}
        ${this._config.show_summary ? this._renderSummary(summary) : ''}
      </ha-card>
    `;
  }

  /** 获取日期显示字符串 */
  private _getDateDisplay(): string {
    const now = new Date();
    const month = now.getMonth() + 1;
    const day = now.getDate();
    const weekday = this._getTodayWeekday();
    return `${month}月${day}日 ${weekday}`;
  }

  /** 获取今天是星期几（中文，使用本地时区） */
  private _getTodayWeekday(): string {
    const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
    return weekdays[new Date().getDay()];
  }

  /** 获取今日日期字符串（YYYY-MM-DD，使用本地时区） */
  private _getTodayDate(): string {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  /** 解析喂食计划 */
  private _parseTodayPlans(attrs: any): FeedingPlanItem[] {
    const weekday = this._getTodayWeekday();
    const scheduleCn = attrs.schedule_cn || attrs.schedule || {};
    const todayPlans = scheduleCn[weekday] || [];
    const isEnabled = attrs.is_executed !== 0;

    return todayPlans.map((item: any, index: number) => {
      return {
        id: `${weekday}_${index}`,
        itemId: item.id,
        name: item.name || `${weekday}喂食`,
        time: item.time || '',
        amount: item.portions || item.amount || 0,
        is_enabled: isEnabled,
        is_completed: false,
        enabled: isEnabled,
      };
    });
  }

  /** 解析今日喂食记录 */
  private _parseTodayRecords(attrs: any, today: string): FeedingRecord[] {
    const history = attrs.history || {};
    const todayRecords = history[today] || [];

    return todayRecords.map((item: any) => {
      return {
        id: item.id,
        date: today,
        time: item.time || '',
        name: item.name || '',
        amount: item.amount || 0,
        real_amount: item.real_amount || item.amount || 0,
        status: item.status || 0,
        is_executed: item.is_executed !== false,
        is_completed: item.is_completed === true,
        completed_at: item.completed_at,
        src: item.src,
      };
    });
  }

  /** 合并时间线 */
  private _mergeTimeline(plans: FeedingPlanItem[], records: FeedingRecord[]): TimelineItem[] {
    const planItems: TimelineItem[] = plans.map((plan, index) => {
      const timeParts = plan.time.split(':');
      const timeSeconds = parseInt(timeParts[0]) * 3600 + parseInt(timeParts[1]) * 60;
      
      return {
        id: `plan_${plan.time}_${index}`,
        itemId: `s${timeSeconds}`,
        time: plan.time,
        timeSeconds: timeSeconds,
        name: plan.name,
        itemType: 'plan' as const,
        plannedAmount: plan.amount,
        isExecuted: false,
        isEnabled: plan.enabled,
        canDisable: true,
        canDelete: true,
      };
    });

    const TIME_TOLERANCE = 120;

    const recordItems: (TimelineItem | null)[] = records.map((record, index) => {
      let matchedPlan: TimelineItem | undefined;
      
      if (record.src === 1) {
        const recordTimeParts = record.time.split(':');
        const recordTimeSeconds = parseInt(recordTimeParts[0]) * 3600 + parseInt(recordTimeParts[1]) * 60;
        
        matchedPlan = planItems.find(p => {
          const timeDiff = Math.abs((p.timeSeconds || 0) - recordTimeSeconds);
          const nameMatch = p.name === record.name;
          const timeMatch = timeDiff <= TIME_TOLERANCE;
          return nameMatch && timeMatch;
        });
      }

      if (matchedPlan) {
        matchedPlan.isExecuted = record.is_completed;
        matchedPlan.actualAmount = record.real_amount;
        matchedPlan.completedAt = record.completed_at;
        
        const pendingChange = this._pendingPlanChanges.get(matchedPlan.itemId);
        if (pendingChange?.enabled !== undefined) {
          matchedPlan.isEnabled = pendingChange.enabled;
          matchedPlan.status = pendingChange.enabled ? 0 : 1;
        } else {
          matchedPlan.isEnabled = record.status === 0;
          matchedPlan.status = record.status;
        }
        
        return null;
      }
      
      const timeParts = record.time.split(':');
      const timeSeconds = parseInt(timeParts[0]) * 3600 + parseInt(timeParts[1]) * 60;
      
      if (record.src === 1) {
        return {
          id: `deleted_plan_${record.time}_${index}`,
          itemId: `s${timeSeconds}`,
          time: record.time,
          timeSeconds: timeSeconds,
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
        id: `manual_${record.time}_${index}`,
        itemId: `s${timeSeconds}`,
        time: record.time,
        timeSeconds: timeSeconds,
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

  private _processTodayData(planAttrs: any, historyAttrs: any) {
    const today = this._getTodayDate();
    const plans = this._parseTodayPlans(planAttrs);
    const records = this._parseTodayRecords(historyAttrs, today);
    let timeline = this._mergeTimeline(plans, records);
    
    if (this._pendingNewItem) {
      const newItem: TimelineItem = {
        id: this._pendingNewItem.itemId,
        itemId: this._pendingNewItem.itemId,
        time: this._pendingNewItem.time,
        name: this._pendingNewItem.name,
        itemType: 'plan',
        plannedAmount: this._pendingNewItem.amount,
        isExecuted: false,
        isEnabled: true,
        canDisable: true,
        canDelete: true,
      };
      timeline.push(newItem);
      timeline.sort((a, b) => a.time.localeCompare(b.time));
    }
    
    const summary = this._getSummaryFromAttrs(historyAttrs, timeline);

    return { timeline, summary };
  }

  private _getSummaryFromAttrs(historyAttrs: any, timeline: TimelineItem[]): TodaySummary {
    const planAmount = historyAttrs.today_plan_amount || 0;
    const actualAmount = historyAttrs.today_real_amount || 0;
    const totalCount = historyAttrs.today_count || timeline.length;
    const completedCount = historyAttrs.today_completed_count || timeline.filter(item => item.isExecuted).length;
    const pendingCount = totalCount - completedCount;

    const isOnline = timeline.length > 0;

    const executedItems = timeline.filter(item => item.isExecuted && item.completedAt);
    const lastFeedingItem = executedItems.length > 0
      ? executedItems.reduce((latest, current) => 
          current.completedAt! > latest.completedAt! ? current : latest
        )
      : undefined;

    const manualAmount = timeline
      .filter(item => item.itemType === 'manual' && item.isExecuted)
      .reduce((sum, item) => sum + (item.actualAmount || 0), 0);

    return {
      planAmount,
      actualAmount,
      manualAmount,
      isOnline,
      lastFeedingTime: lastFeedingItem?.completedAt,
      lastFeedingAmount: lastFeedingItem?.actualAmount,
      totalCount,
      completedCount,
      pendingCount,
    };
  }

  /** 渲染时间线 */
  private _renderTimeline(timeline: TimelineItem[]) {
    if (!timeline.length) {
      return html`
        <div class="section">
          <div class="empty-state">
            <ha-icon .icon=${'mdi:calendar-blank'}></ha-icon>
            <p>暂无喂食计划</p>
          </div>
        </div>
      `;
    }

    return html`
      <div class="section">
        <div class="timeline-list">
          ${timeline.filter(item => {
            const pendingChange = this._pendingPlanChanges.get(item.itemId);
            const isPlanDeleted = pendingChange?.deleted || item.itemType === 'deleted_plan';
            return !(isPlanDeleted && !item.isExecuted);
          }).map(item => this._renderTimelineItem(item))}
        </div>
      </div>
    `;
  }

  /** 渲染时间线条目（紧凑版本） */
  private _renderTimelineItem(item: TimelineItem) {
    const pendingChange = this._pendingPlanChanges.get(item.itemId);
    const isPlanDeleted = pendingChange?.deleted || item.itemType === 'deleted_plan';
    
    const displayTime = pendingChange?.time || item.time;
    const displayName = pendingChange?.name || item.name;
    const displayAmount = pendingChange?.amount ?? item.plannedAmount;
    
    const amount = item.actualAmount !== undefined ? item.actualAmount : displayAmount;
    const isManualFeed = item.itemType === 'manual';
    const canEdit = item.itemType === 'plan' && !isPlanDeleted;
    const editField = this._editingItem?.itemId === item.itemId ? this._editingItem?.field : null;
    
    const statusIconHtml = item.isExecuted
      ? html`
          <svg viewBox="4 4 92 92" class="status-icon done">
            <circle cx="50" cy="50" r="40" fill="none" stroke="rgb(74,222,119)" stroke-width="12"/>
            <line x1="45" y1="70" x2="70" y2="40" stroke="rgb(74,222,119)" stroke-width="15" stroke-linecap="round"/>
            <line x1="28" y1="50" x2="45" y2="70" stroke="rgb(74,222,119)" stroke-width="15" stroke-linecap="round"/>
          </svg>
        `
      : html`
          <svg viewBox="4 4 92 92" class="status-icon pending">
            <circle cx="50" cy="50" r="40" fill="none" stroke="rgb(156,163,175)" stroke-width="12"/>
            <line x1="45" y1="70" x2="70" y2="40" stroke="rgb(156,163,175)" stroke-width="15" stroke-linecap="round"/>
            <line x1="28" y1="50" x2="45" y2="70" stroke="rgb(156,163,175)" stroke-width="15" stroke-linecap="round"/>
          </svg>
        `;

    const deleteIconSvg = svg`
      <svg viewBox="4 4 92 92" class="delete-icon">
        <circle cx="50" cy="50" r="40" fill="none" stroke="#ff0000" stroke-width="12"/>
        <line x1="35" y1="50" x2="65" y2="50" stroke="#ff0000" stroke-width="15" stroke-linecap="round"/>
      </svg>
    `;

    const canToggle = item.itemType === 'plan' && !item.isExecuted && !isPlanDeleted;
    const canDeleteBtn = item.itemType === 'plan' && item.canDelete && !isPlanDeleted;

    const editData = this._editingItem;
    
    const focusInput = (el: Element | undefined) => {
      if (el && (el instanceof HTMLInputElement)) {
        requestAnimationFrame(() => {
          el.focus();
          el.select?.();
          if (el.type === 'time') {
            el.showPicker?.();
          }
        });
      }
    };

    const timeEl = editField === 'time' && editData
      ? html`
          <input 
            ${ref(focusInput)}
            type="time" 
            class="edit-time" 
            .value=${editData.time}
            @change=${(e: Event) => { this._editingItem!.time = (e.target as HTMLInputElement).value; }}
            @keydown=${(e: KeyboardEvent) => { if (e.key === 'Escape') this._cancelEdit(); }}
          />
        `
      : html`<span class="time ${canEdit ? 'editable' : ''}" @click=${canEdit ? () => this._startEdit(item, 'time') : undefined}>${displayTime}</span>`;

    const nameEl = editField === 'name' && editData
      ? html`
          <input 
            ${ref(focusInput)}
            type="text" 
            class="edit-name" 
            .value=${editData.name}
            @change=${(e: Event) => { this._editingItem!.name = (e.target as HTMLInputElement).value; }}
            @keydown=${(e: KeyboardEvent) => { if (e.key === 'Escape') this._cancelEdit(); }}
            placeholder="名称"
          />
        `
      : html`<span class="name ${canEdit ? 'editable' : ''}" @click=${canEdit ? () => this._startEdit(item, 'name') : undefined}>${displayName}</span>`;

    const amountEl = editField === 'amount' && editData
      ? html`
          <input 
            ${ref(focusInput)}
            type="number" 
            class="edit-amount" 
            .value=${String(editData.amount)}
            min="1" max="100"
            @change=${(e: Event) => { this._editingItem!.amount = parseInt((e.target as HTMLInputElement).value) || 10; }}
            @keydown=${(e: KeyboardEvent) => { if (e.key === 'Escape') this._cancelEdit(); }}
          />
        `
      : html`<span class="amount ${canEdit ? 'editable' : ''}" @click=${canEdit ? () => this._startEdit(item, 'amount') : undefined}>${amount}g</span>`;

    return html`
      <div class="timeline-item ${item.itemType} ${editField ? 'editing' : ''} ${isPlanDeleted ? 'plan-deleted' : ''}">
        <div class="item-row">
          ${timeEl}
          ${nameEl}
          ${amountEl}
          ${statusIconHtml}
          <div class="item-actions">
            ${this._config?.show_actions
              ? html`
                  <div 
                    class="toggle-switch ${item.isEnabled ? 'on' : 'off'} ${!canToggle ? 'disabled' : ''}"
                    @click=${canToggle ? () => this._togglePlan(item) : undefined}
                    title="${isManualFeed ? '手动喂食' : (isPlanDeleted ? '已删除计划' : (item.isExecuted ? '已执行' : (item.isEnabled ? '点击禁用计划' : '点击启用计划')))}"
                  >
                    <div class="toggle-thumb"></div>
                  </div>
                  <button 
                    class="icon-delete-btn ${!canDeleteBtn ? 'disabled' : ''}" 
                    @click=${canDeleteBtn ? () => this._deletePlan(item) : undefined}
                    title="${isManualFeed ? '手动喂食' : (isPlanDeleted ? '已删除计划' : '删除计划')}"
                    ?disabled=${!canDeleteBtn}
                  >
                    ${deleteIconSvg}
                  </button>
                `
              : ''}
          </div>
        </div>
      </div>
    `;
  }

  /** 渲染新增计划按钮 */
  private _renderAddPlanButton() {
    return html`
      <div class="timeline-list-footer">
        <button class="add-plan-btn" @click=${this._handleAddPlan} title="新增计划">
          <span class="add-plus"></span>
        </button>
      </div>
    `;
  }

  /** 渲染统计区域 */
  private _renderSummary(summary: TodaySummary) {
    return html`
      <div class="summary-row">
        <span class="summary-item">
          <span class="summary-label">在线状态</span>
          <span class="summary-value">${summary.isOnline ? '在线' : '离线'}</span>
        </span>
        <span class="summary-item">
          <span class="summary-label">计划喂食</span>
          <span class="summary-value">${summary.planAmount}g</span>
        </span>
        <span class="summary-item">
          <span class="summary-label">实际喂食</span>
          <span class="summary-value">${summary.actualAmount}g</span>
        </span>
        <span class="summary-item">
          <span class="summary-label">手动喂食</span>
          <span class="summary-value">${summary.manualAmount}g</span>
        </span>
      </div>
    `;
  }

  /** 操作：手动喂食 */
  private async _handleManualFeed(): Promise<void> {
    if (!this.hass || !this._config) {
      return;
    }
    
    const feedEntity = this._getManualFeedEntity();
    
    if (feedEntity) {
      try {
        await this.hass.callService('button', 'press', {
          entity_id: feedEntity
        });
      } catch (error) {
        console.error('[PetkitSoloCard] 手动喂食失败:', error);
      }
    }
  }
  
  /** 获取手动喂食按钮实体ID */
  private _getManualFeedEntity(): string | null {
    if (this.hass) {
      for (const entityId in this.hass.states) {
        if (entityId.startsWith('button.') && entityId.includes('petkit')) {
          const state = this.hass.states[entityId];
          const friendlyName = state?.attributes?.friendly_name || '';
          if (friendlyName.includes('手动') || friendlyName.includes('出粮') || 
              friendlyName.toLowerCase().includes('feed')) {
            if (!friendlyName.includes('刷新') && !friendlyName.toLowerCase().includes('refresh')) {
              return entityId;
            }
          }
        }
      }
    }
    
    return null;
  }

  /** 操作：刷新 */
  private async _handleRefresh(): Promise<void> {
    if (!this.hass || !this._config) {
      return;
    }
    
    const refreshEntity = this._getRefreshEntity();
    
    if (refreshEntity) {
      try {
        await this.hass.callService('button', 'press', {
          entity_id: refreshEntity
        });
      } catch (error) {
        console.error('[PetkitSoloCard] 刷新失败:', error);
      }
    }
  }
  
  /** 获取刷新按钮实体ID */
  private _getRefreshEntity(): string | null {
    if (this._config?.refresh_entity) {
      return this._config.refresh_entity;
    }
    
    if (this.hass) {
      for (const entityId in this.hass.states) {
        if (entityId.startsWith('button.') && entityId.includes('petkit')) {
          const state = this.hass.states[entityId];
          const friendlyName = state?.attributes?.friendly_name || '';
          if (friendlyName.includes('刷新') || friendlyName.toLowerCase().includes('refresh')) {
            return entityId;
          }
        }
      }
    }
    
    return null;
  }

  /** 操作：切换计划启用状态 */
  private async _togglePlan(item: TimelineItem): Promise<void> {
    if (!this.hass || !this._config) {
      return;
    }
    
    if (item.isExecuted) {
      return;
    }
    
    const newEnabled = !item.isEnabled;
    
    if (item.isEnabled === newEnabled) {
      return;
    }
    
    const day = new Date().getDay();
    const weekday = day === 0 ? 7 : day;
    
    this._pendingPlanChanges.set(item.itemId, {
      time: item.time,
      name: item.name,
      amount: item.plannedAmount,
      enabled: newEnabled,
    });
    this.requestUpdate();
    
    try {
      await this.hass.callService('petkit_solo', 'toggle_feeding_item', {
        day: weekday,
        item_id: item.itemId,
        enabled: newEnabled
      });
      this._pendingPlanChanges.delete(item.itemId);
    } catch (error) {
      this._pendingPlanChanges.delete(item.itemId);
      this.requestUpdate();
      console.error('[PetkitSoloCard] 切换失败:', error);
      alert(`切换失败: ${error}`);
    }
  }

  /** 操作：删除计划 */
  private async _deletePlan(item: TimelineItem): Promise<void> {
    if (!this.hass || !this._config) {
      return;
    }
    
    if (this._pendingNewItem?.itemId === item.itemId) {
      this._pendingNewItem = null;
      this._editingItem = null;
      this._originalItemData = null;
      if (this._saveTimeout) {
        clearTimeout(this._saveTimeout);
        this._saveTimeout = null;
      }
      this.requestUpdate();
      return;
    }
    
    const pendingChange = this._pendingPlanChanges.get(item.itemId);
    if (pendingChange?.deleted) {
      return;
    }
    
    const day = new Date().getDay();
    const weekday = day === 0 ? 7 : day;
    
    console.log('[PetkitSoloCard] 删除计划:', {
      day: weekday,
      item_id: item.itemId,
      item_name: item.name,
      item_time: item.time
    });
    
    this._pendingPlanChanges.set(item.itemId, {
      time: item.time,
      name: item.name,
      amount: item.plannedAmount,
      deleted: true,
    });
    this.requestUpdate();
    
    try {
      await this.hass.callService('petkit_solo', 'remove_feeding_item', {
        day: weekday,
        item_id: item.itemId
      });
      console.log('[PetkitSoloCard] 删除计划成功');
    } catch (error) {
      console.error('[PetkitSoloCard] 删除计划失败:', error);
      this._pendingPlanChanges.delete(item.itemId);
      this.requestUpdate();
    }
  }

  /** 操作：开始编辑 */
  private _startEdit(item: TimelineItem, field: 'time' | 'name' | 'amount'): void {
    if (this._saveTimeout) {
      clearTimeout(this._saveTimeout);
      this._saveTimeout = null;
    }
    
    if (this._pendingNewItem?.itemId === item.itemId) {
      this._editingItem = {
        itemId: item.itemId,
        field: field,
        time: this._pendingNewItem.time,
        name: this._pendingNewItem.name,
        amount: this._pendingNewItem.amount,
      };
      this._originalItemData = {
        time: this._pendingNewItem.time,
        name: this._pendingNewItem.name,
        amount: this._pendingNewItem.amount,
      };
      this.requestUpdate();
      return;
    }
    
    const pendingChange = this._pendingPlanChanges.get(item.itemId);
    const editTime = pendingChange?.time || item.time;
    const editName = pendingChange?.name || item.name;
    const editAmount = pendingChange?.amount ?? item.plannedAmount;
    
    this._editingItem = {
      itemId: item.itemId,
      field: field,
      time: editTime,
      name: editName,
      amount: editAmount,
    };
    this._originalItemData = {
      time: editTime,
      name: editName,
      amount: editAmount,
    };
    this.requestUpdate();
  }

/** 操作：新增计划 */
  private _handleAddPlan(): void {
    if (!this.hass || !this._config) {
      return;
    }
    
    if (this._saveTimeout) {
      clearTimeout(this._saveTimeout);
      this._saveTimeout = null;
    }
    
    const newItemId = `new_${Date.now()}`;
    
    this._pendingNewItem = {
      itemId: newItemId,
      time: '00:00',
      name: '早餐',
      amount: 10,
    };
    
    this._editingItem = {
      itemId: newItemId,
      field: 'name',
      time: '00:00',
      name: '早餐',
      amount: 10,
    };
    
    this._originalItemData = {
      time: '00:00',
      name: '早餐',
      amount: 10,
    };
    
    console.log('[PetkitSoloCard] 新增计划:', newItemId);
    this.requestUpdate();
  }

  /** 卡片失焦处理 */
  private _handleCardFocusOut(e: FocusEvent): void {
    const relatedTarget = e.relatedTarget as Element;
    if (relatedTarget && this.contains(relatedTarget)) {
      return;
    }
    
    if (this._saveTimeout) {
      clearTimeout(this._saveTimeout);
    }
    
    this._saveTimeout = window.setTimeout(() => {
      this._doSavePendingChanges();
    }, 100);
  }

  /** 执行待保存的修改 */
  private _doSavePendingChanges(): void {
    if (this._pendingNewItem && this._editingItem) {
      const hasChanges = this._originalItemData && (
        this._editingItem.time !== this._originalItemData.time ||
        this._editingItem.name !== this._originalItemData.name ||
        this._editingItem.amount !== this._originalItemData.amount
      );
      
      this._pendingNewItem.time = this._editingItem.time;
      this._pendingNewItem.name = this._editingItem.name;
      this._pendingNewItem.amount = this._editingItem.amount;
      
      this._editingItem = null;
      this._originalItemData = null;
      
      if (hasChanges) {
        this._saveNewItem();
      }
    } else if (this._editingItem) {
      const editData = { ...this._editingItem };
      const originalData = this._originalItemData;
      
      this._editingItem = null;
      this._originalItemData = null;
      
      const hasChanges = originalData && (
        editData.time !== originalData.time ||
        editData.name !== originalData.name ||
        editData.amount !== originalData.amount
      );
      
      if (hasChanges) {
        this._pendingPlanChanges.set(editData.itemId, {
          time: editData.time,
          name: editData.name,
          amount: editData.amount,
        });
        this.requestUpdate();
        this._updateExistingItem(editData);
      }
    }
    
    this.requestUpdate();
  }
  
  private async _updateExistingItem(
    editData: { itemId: string; time: string; name: string; amount: number }
  ): Promise<void> {
    if (!this.hass) {
      return;
    }
    
    const day = new Date().getDay();
    const weekday = day === 0 ? 7 : day;
    
    console.log('[PetkitSoloCard] 更新计划:', {
      day: weekday,
      item_id: editData.itemId,
      time: editData.time,
      amount: editData.amount,
      name: editData.name,
    });
    
    try {
      await this.hass.callService('petkit_solo', 'update_feeding_item', {
        day: weekday,
        item_id: editData.itemId,
        time: editData.time,
        amount: editData.amount,
        name: editData.name,
      });
      console.log('[PetkitSoloCard] 更新计划成功');
      this._pendingPlanChanges.delete(editData.itemId);
    } catch (error) {
      console.error('[PetkitSoloCard] 更新计划失败:', error);
      this._pendingPlanChanges.delete(editData.itemId);
      this.requestUpdate();
    }
  }

  /** 操作：取消编辑 */
  private _cancelEdit(): void {
    this._editingItem = null;
    this._originalItemData = null;
    this._pendingNewItem = null;
    if (this._saveTimeout) {
      clearTimeout(this._saveTimeout);
      this._saveTimeout = null;
    }
    this.requestUpdate();
  }

  private async _saveNewItem(): Promise<void> {
    if (!this.hass || !this._pendingNewItem) {
      return;
    }
    
    const planEntity = this._config?.entity ? this.hass.states[this._config.entity] : null;
    if (planEntity) {
      const scheduleCn = planEntity.attributes?.schedule_cn || planEntity.attributes?.schedule || {};
      const weekday = new Date().getDay() || 7;
      const weekdayNames = ['', '周一', '周二', '周三', '周四', '周五', '周六', '周日'];
      const todayPlans = scheduleCn[weekdayNames[weekday]] || [];
      
      const existingPlan = todayPlans.find((p: any) => p.time === this._pendingNewItem!.time);
      
      if (existingPlan) {
        console.log('[PetkitSoloCard] 该时间点已存在计划，跳过保存');
        this._pendingNewItem = null;
        this.requestUpdate();
        return;
      }
    }
    
    const day = new Date().getDay();
    const weekday = day === 0 ? 7 : day;
    
    console.log('[PetkitSoloCard] 保存新计划:', {
      day: weekday,
      time: this._pendingNewItem.time,
      amount: this._pendingNewItem.amount,
      name: this._pendingNewItem.name,
    });
    
    try {
      await this.hass.callService('petkit_solo', 'add_feeding_item', {
        day: weekday,
        time: this._pendingNewItem.time,
        amount: this._pendingNewItem.amount,
        name: this._pendingNewItem.name,
      });
      console.log('[PetkitSoloCard] 保存新计划成功');
      this._pendingNewItem = null;
      this.requestUpdate();
    } catch (error) {
      console.error('[PetkitSoloCard] 保存新计划失败:', error);
    }
  }

static styles = css`
    :host {
      display: block;
    }
    
    ha-card {
      padding: 10px;
    }
    
    /* 头部 */
    .header {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 8px;
      padding-bottom: 6px;
      border-bottom: 1px solid var(--divider-color);
    }
    
    .header-title {
      font-size: 12px;
      font-weight: bold;
    }
    
    .header-date {
      font-size: 10px;
      color: var(--secondary-text-color);
      flex: 1;
      text-align: center;
    }
    
    .header-actions {
      display: flex;
      align-items: center;
      gap: 6px;
    }
    
    /* 统一的图标按钮样式 */
    .icon-btn {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 32px;
      height: 32px;
      padding: 0;
      border: none;
      background: transparent;
      cursor: pointer;
      border-radius: 50%;
      transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
      position: relative;
      overflow: hidden;
    }
    
    .icon-btn::before {
      content: '';
      position: absolute;
      inset: 0;
      background: currentColor;
      opacity: 0;
      transition: opacity 0.2s;
    }
    
    .icon-btn:hover::before {
      opacity: 0.1;
    }
    
    .icon-btn:active {
      transform: scale(0.92);
    }
    
    .icon-btn:focus {
      outline: 2px solid var(--primary-color, #03a9f4);
      outline-offset: 2px;
    }
    
    .btn-svg {
      width: 18px;
      height: 18px;
      fill: currentColor;
      transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    /* 刷新按钮 - 旋转动画 */
    .refresh-btn {
      color: var(--primary-text-color, #212121);
    }
    
    .refresh-btn:hover .btn-svg {
      transform: rotate(180deg);
    }
    
    /* 手动喂食按钮 - 主要操作，突出显示 */
    .feed-btn {
      width: 36px;
      height: 36px;
      background: var(--primary-color, #03a9f4);
      color: white;
      box-shadow: 0 0 0 1px rgba(3, 169, 244, 0.1), 0 0 8px 2px rgba(3, 169, 244, 0.3);
    }
    
    .feed-btn::before {
      background: white;
    }
    
    .feed-btn:hover {
      box-shadow: 0 0 0 1px rgba(3, 169, 244, 0.15), 0 0 12px 3px rgba(3, 169, 244, 0.4);
    }
    
    .feed-btn:active {
      transform: scale(0.95);
    }
    
    .feed-btn .btn-svg {
      width: 20px;
      height: 20px;
    }
    
    .feed-btn:hover .btn-svg {
      transform: scale(1.1);
    }
    
    /* 区块 */
    .section {
      margin-bottom: 8px;
    }
    
    /* 时间线条目（紧凑布局） */
    .timeline-list {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    
    .timeline-item {
      border: 1px solid var(--divider-color);
      border-radius: 6px;
      padding: 8px 10px;
      background: var(--card-background-color);
    }
    
    .timeline-item.manual {
      background: var(--secondary-background-color);
    }
    
    .item-row {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 0;
    }
    
    .time {
      font-weight: bold;
      font-size: 12px;
      color: var(--primary-text-color);
      flex-shrink: 0;
      width: 55px;
    }
    
    .name {
      font-size: 11px;
      color: var(--secondary-text-color);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      flex: 1 1 auto;
      min-width: 14px;
    }
    
    .amount {
      font-weight: bold;
      font-size: 11px;
      color: var(--primary-color);
      flex-shrink: 0;
      width: 40px;
      text-align: center;
    }
    
    .status-icon {
      flex-shrink: 0;
    }
    
    .item-actions {
      flex-shrink: 0;
    }
    
    .time.editable, .name.editable, .amount.editable {
      cursor: pointer;
      padding: 2px 4px;
      border-radius: 4px;
      transition: background-color 0.2s;
    }
    
    .time.editable:hover, .name.editable:hover, .amount.editable:hover {
      background-color: var(--primary-color, #03a9f4);
      color: white;
    }
    
    /* 编辑模式 */
    .timeline-item.editing {
      background-color: rgba(3, 169, 244, 0.1);
      border: 1px solid var(--primary-color, #03a9f4);
    }
    
    .edit-time, .edit-name, .edit-amount {
      font-size: 11px;
      font-family: inherit;
      padding: 2px 3px;
      border: 1px solid var(--primary-color, #03a9f4);
      border-radius: 4px;
      outline: none;
      background: white;
      color: #333;
    }
    
    .edit-time:focus, .edit-name:focus, .edit-amount:focus {
      border-color: var(--primary-color, #03a9f4);
      box-shadow: 0 0 0 1px var(--primary-color, #03a9f4);
    }
    
    .edit-time {
      width: 55px;
      min-width: 55px;
      max-width: 55px;
      padding: 0;
      text-align: center;
      cursor: pointer;
      position: relative;
    }
    
    .edit-time::-webkit-calendar-picker-indicator {
      position: absolute;
      left: 0;
      right: 0;
      width: 100%;
      height: 100%;
      margin: 0;
      padding: 0;
      cursor: pointer;
      opacity: 0;
    }
    
    .edit-time::-webkit-datetime-edit {
      padding: 2px 4px;
      display: flex;
      justify-content: center;
    }
    
    .edit-time::-webkit-datetime-edit-fields-wrapper {
      padding: 0;
      display: flex;
      justify-content: center;
    }
    
    .edit-time::-webkit-datetime-edit-text {
      color: #333;
      padding: 0 1px;
    }
    
    .edit-time::-webkit-datetime-edit-hour-field,
    .edit-time::-webkit-datetime-edit-minute-field {
      color: #333;
      font-weight: bold;
      padding: 0 1px;
      background: transparent;
    }
    
    .edit-time::-webkit-datetime-edit-hour-field:focus,
    .edit-time::-webkit-datetime-edit-minute-field:focus {
      background: transparent;
      outline: none;
    }
    
    .edit-name {
      flex: 1 1 auto;
      min-width: 14px;
    }
    
    .edit-amount {
      width: 40px;
      min-width: 40px;
      max-width: 40px;
      padding: 2px 3px;
      text-align: center;
    }
    
    .edit-btn {
      padding: 4px 8px;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: 12px;
      font-weight: bold;
    }
    
    .edit-btn.save {
      background-color: var(--success-color, #4caf50);
      color: white;
    }
    
    .edit-btn.cancel {
      background-color: #ccc;
      color: #333;
    }
    
    .edit-btn:hover {
      opacity: 0.8;
    }
    
    /* 状态图标 */
    .status-icon {
      width: 16px;
      height: 16px;
      flex-shrink: 0;
      transition: transform 0.2s ease;
    }
    
    .status-icon:hover {
      transform: scale(1.1);
    }
    
    .status-icon.done {
      /* 绿色对号 */
    }
    
    .status-icon.pending {
      /* 灰色对号，绿色圆环 */
    }
    
    .status-done {
      color: var(--success-color, #4caf50);
    }
    
    .status-pending {
      color: var(--warning-color, #ff9800);
    }
    
    .item-actions {
      display: flex;
      gap: 8px;
      align-items: center;
      justify-content: flex-end;
    }
    
    /* 新增计划按钮 */
    .add-plan-btn {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 100%;
      height: 24px;
      padding: 0;
      border: 1px dashed var(--divider-color);
      background: transparent;
      cursor: pointer;
      border-radius: 6px;
      transition: all 0.2s ease;
    }
    
    .add-plan-btn:hover {
      border-color: var(--primary-color, #03a9f4);
      background: rgba(3, 169, 244, 0.05);
    }
    
    .add-plan-btn:hover .add-plus,
    .add-plan-btn:hover .add-plus::after {
      background: var(--primary-color, #03a9f4);
    }
    
    .add-plan-btn:active {
      transform: scale(0.98);
    }
    
    .add-plus {
      position: relative;
      width: 16px;
      height: 2px;
      background: var(--secondary-text-color, #757575);
      border-radius: 2px;
      transition: background 0.2s ease;
    }
    
    .add-plus::after {
      content: '';
      position: absolute;
      top: -7px;
      left: 7px;
      width: 2px;
      height: 16px;
      background: var(--secondary-text-color, #757575);
      border-radius: 2px;
      transition: background 0.2s ease;
    }
    
    /* 删除图标按钮 */
    .icon-delete-btn {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 16px;
      height: 16px;
      padding: 0;
      border: none;
      background: transparent;
      cursor: pointer;
      border-radius: 50%;
      transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
      position: relative;
      overflow: visible;
    }
    
    .icon-delete-btn::before {
      content: '';
      position: absolute;
      inset: -6px;
      background: var(--error-color, #f44336);
      opacity: 0;
      transition: opacity 0.2s;
      border-radius: 50%;
      z-index: -1;
    }
    
    .icon-delete-btn:hover::before {
      opacity: 0.15;
    }
    
    .icon-delete-btn:active {
      transform: scale(0.9);
    }
    
    .delete-icon {
      width: 16px;
      height: 16px;
      fill: var(--secondary-text-color, #757575);
      transition: transform 0.2s ease;
    }
    
    .icon-delete-btn:hover .delete-icon {
      fill: var(--error-color, #f44336);
      transform: scale(1.1);
    }
    
    /* 禁用状态的按钮 */
    .icon-delete-btn.disabled {
      cursor: not-allowed;
      opacity: 0.4;
    }
    
    .icon-delete-btn.disabled:hover::before {
      opacity: 0;
    }
    
    .icon-delete-btn.disabled:hover .delete-icon {
      fill: var(--secondary-text-color, #757575);
      transform: none;
    }
    
    /* 开关样式 */
    .toggle-switch {
      position: relative;
      width: 28px;
      height: 16px;
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.2s ease;
      flex-shrink: 0;
    }
    
    .toggle-switch:hover {
      transform: scale(1.1);
    }
    
    .toggle-switch.on {
      background: var(--primary-color, #03a9f4);
    }
    
    .toggle-switch.off {
      background: var(--disabled-color, #bdbdbd);
    }
    
    .toggle-switch.disabled {
      cursor: not-allowed;
      opacity: 0.4;
    }
    
    .toggle-switch.disabled:hover {
      transform: none;
    }
    
    .toggle-thumb {
      position: absolute;
      top: 2px;
      width: 12px;
      height: 12px;
      border-radius: 50%;
      background: white;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .toggle-switch.on .toggle-thumb {
      transform: translateX(14px);
    }
    
    .toggle-switch.off .toggle-thumb {
      transform: translateX(2px);
    }
    
    .toggle-switch:hover .toggle-thumb {
      box-shadow: 0 2px 5px rgba(0, 0, 0, 0.25);
    }
    
    .toggle-switch:active .toggle-thumb {
      width: 16px;
    }
    
    .toggle-switch.on:active .toggle-thumb {
      transform: translateX(10px);
    }
    
    .toggle-switch.off:active .toggle-thumb {
      transform: translateX(0px);
    }
    
    /* 禁用状态的计划项 */
    .timeline-item.disabled {
      opacity: 0.5;
    }
    
    .timeline-item.disabled .time,
    .timeline-item.disabled .name,
    .timeline-item.disabled .amount {
      text-decoration: line-through;
    }
    
    /* 已删除计划的记录项 */
    .timeline-item.plan-deleted {
      opacity: 0.4;
    }
    
    .timeline-item.plan-deleted .time,
    .timeline-item.plan-deleted .name,
    .timeline-item.plan-deleted .amount {
      color: var(--disabled-text-color, #9e9e9e);
    }
    
    .action-btn {
      --mdc-typography-button-font-size: 11px;
      --mdc-button-horizontal-padding: 6px;
      --mdc-button-vertical-padding: 3px;
      min-width: auto;
    }
    
    .action-btn.danger {
      --mdc-theme-primary: var(--error-color, #f44336);
    }
    
    /* 时间线列表底部（新增计划按钮） */
    .timeline-list-footer {
      margin-top: 6px;
      margin-bottom: 8px;
    }
    
    /* 统计行 */
    .summary-row {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      align-items: center;
      padding: 6px 8px;
      border: 1px solid var(--divider-color);
      border-radius: 6px;
      background: var(--card-background-color);
    }
    
    .summary-item {
      display: flex;
      flex-direction: column;
      gap: 1px;
      text-align: center;
    }
    
    .summary-item:not(:last-child) {
      border-right: 1px solid var(--divider-color);
    }
    
    .summary-label {
      font-size: 9px;
      color: var(--secondary-text-color);
    }
    
    .summary-value {
      font-size: 12px;
      font-weight: bold;
      color: var(--primary-text-color);
    }
    
    /* 空状态 */
    .empty-state {
      text-align: center;
      padding: 16px 0;
      color: var(--secondary-text-color);
    }
    
    .empty-state ha-icon {
      --mdc-icon-size: 32px;
      margin-bottom: 8px;
      opacity: 0.5;
    }
    
    .empty-state p {
      margin: 0;
      font-size: 12px;
    }
    
    /* 错误状态 */
    .error-state {
      text-align: center;
      padding: 16px 0;
      color: var(--error-color, #f44336);
    }
    
    .error-state ha-icon {
      --mdc-icon-size: 32px;
      margin-bottom: 8px;
    }
    
    .error-state p {
      margin: 0;
      font-size: 12px;
    }
  `;
}

// 显式注册自定义元素
if (!customElements.get('petkit-solo-card')) {
  customElements.define('petkit-solo-card', PetkitSoloCard);
}
