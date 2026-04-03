/** 小佩喂食器卡片 - 主组件 */

import { LitElement, html, svg } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import { HomeAssistant } from 'custom-card-helpers';
import { PetkitSoloCardConfig, TimelineItem, TodaySummary } from './types';
import { getEntityId, getTodayWeekdayNumber } from './utils';
import { processWeeklyData } from './data';
import { combineStyles } from './styles';
import { saveFeed, toggleFeedingItem } from './services/plan';
import { WeeklyCacheManager } from './state';
import { WEEKDAY_NAMES } from './utils/constants';

@customElement('petkit-feeder-card')
export class PetkitFeederCard extends LitElement {
  @property({ attribute: false }) public hass!: HomeAssistant;
  @property({ attribute: false }) private _config?: PetkitSoloCardConfig;

  private _weeklyCache: WeeklyCacheManager = new WeeklyCacheManager();
  private _selectedDay: number = 1;
  private _editingItem: { itemId: string; field: 'time' | 'name' | 'amount'; time: string; name: string; amount: number } | null = null;
  private _originalItemData: { time: string; name: string; amount: number } | null = null;
  private _saveDebounceTimer: number | null = null;
  private _isSaving: boolean = false;
  private _pendingFocus: { itemId: string; field: 'time' | 'name' | 'amount' } | null = null;
  private _isAddingNewPlan: boolean = false;  // 标记正在添加新计划

  private _getEntityId(entityType: string): string {
    if (!this._config) return '';
    return getEntityId(this._config, entityType);
  }

  static getStubConfig(): PetkitSoloCardConfig {
    return {
      device_id: '',
      show_timeline: true,
      show_summary: true,
      show_actions: true,
    };
  }

  static getConfigElement() {
    return document.createElement('petkit-feeder-card-editor');
  }

  public setConfig(config: PetkitSoloCardConfig): void {
    if (!config.device_id && !config.entity) {
      throw new Error('需要定义 device_id 或 entity');
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

  protected updated() {
    if (this._pendingFocus) {
      const { itemId, field } = this._pendingFocus;
      const inputId = `edit-${field}-${itemId}`;
      const input = this.shadowRoot?.getElementById(inputId) as HTMLInputElement;
      
      if (input) {
        input.focus();
        if (field === 'name') {
          input.select();
        } else if (field === 'time') {
          input.showPicker?.();
        }
      }
      this._isAddingNewPlan = false;
      this._pendingFocus = null;
    }
  }

  protected render() {
    if (!this._config || !this.hass) {
      return html`<div>加载中...</div>`;
    }

    const planEntityId = this._config.entity || this._getEntityId('feeding_schedule');
    const historyEntityId = this._config.history_entity || this._getEntityId('feeding_records');

    const planEntity = this.hass.states[planEntityId];
    const historyEntity = historyEntityId ? this.hass.states[historyEntityId] : null;

    if (!planEntity) {
      return html`
        <ha-card>
          <div class="error-state">
            <ha-icon .icon=${'mdi:alert-circle'}></ha-icon>
            <p>实体不存在：${planEntityId}</p>
          </div>
        </ha-card>
      `;
    }

    // 处理一周数据
    const weeklyData = processWeeklyData(
      planEntity.attributes,
      historyEntity?.attributes || {}
    );

    // 初始化或更新缓存
    if (!this._weeklyCache.originData) {
      this._weeklyCache.initOrigin(weeklyData);
      this._selectedDay = getTodayWeekdayNumber();
    }

    // 获取当前选中天的数据
    const dayData = this._weeklyCache.getDayCache(this._selectedDay);
    const timeline = dayData?.timeline || [];
    const summary = dayData?.summary || this._emptySummary();

    let deviceName = this._config.name;
    if (!deviceName) {
      const deviceNameEntityId = this._config.device_name_entity || this._getEntityId('device_name');
      const deviceNameEntity = this.hass.states[deviceNameEntityId];
      deviceName = deviceNameEntity?.state;
    }
    if (!deviceName) {
      deviceName = planEntity.attributes.friendly_name || '小佩喂食器';
    }

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
                <path d="M431.424 246.336c36.576-14.208 74.112-1.024 107.04 40.48l-0.32-0.384-2.016-2.464 7.264-3.84c42.432-21.44 83.84-22.304 112 16.128l0.864 1.248 3.552-1.92c34.24-17.376 75.168-2.144 116.832 50.304l5.024 6.496 3.2 4.416c4.16 6.848 6.4 14.4 6.4 22.272l-0.128-2.752 1.76 13.76 2.56 17.664c0.96 6.176 1.984 12.608 3.104 19.328 6.4 38.24 14.368 76.448 24 111.968 9.216 34.08 19.52 63.808 30.24 86.816l2.72 5.76 1.504 3.744c1.6 4.224 2.848 8.448 3.616 12.736 0.608 3.104 0.928 6.176 0.928 9.248 0 69.312-162.336 126.272-343.552 128.352l-10.272 0.064c-186.88 0-353.888-55.232-353.888-125.536 0-7.136 1.408-14.112 3.904-21.76 1.216-3.68 2.56-7.136 4.48-11.936l3.648-9.056c0.736-1.92 1.12-3.2 1.792-5.44a786.496 786.496 0 0 0 43.648-166.016c2.72-18.432 4.448-35.104 5.408-49.664l0.672-13.44 0.096-3.84 0.32-5.184a43.52 43.52 0 0 1 7.264-18.912l2.272-3.488c4.96-8.32 13.568-19.904 25.696-31.552 34.496-33.12 76.672-45.216 121.152-20.16l-2.464-1.312 2.336-3.328c14.4-20.224 31.04-36.48 50.688-45.92z m318.912 183.04c-49.728 25.664-140.224 39.104-245.952 39.104h-10.24c-99.072-0.864-183.712-13.696-232.416-37.44a821.888 821.888 0 0 1-48.48 196l-1.664 5.408a161.76 161.76 0 0 1-2.24 5.696l-2.656 6.528c-1.568 3.84-2.528 6.4-3.296 8.736a25.408 25.408 0 0 0-1.504 6.816c0 29.44 145.504 77.536 305.856 77.536 155.968 0 299.712-48.192 305.6-78.496l0.192-2.016-0.064-0.384a28.256 28.256 0 0 0-1.376-4.512l-1.088-2.688-1.184-2.432c-12.576-26.88-23.68-59.104-33.6-95.648a1218.656 1218.656 0 0 1-25.024-116.608z m-416.096 85.12a24 24 0 0 1 24.16 20.288l0.32 3.648c0.256 28.576-6.496 71.712-26.88 121.92a24 24 0 1 1-44.48-18.08c10.336-25.44 16.96-50.08 20.544-73.056 0.832-5.44 1.472-10.496 1.92-15.168l0.736-9.504 0.128-5.632a24 24 0 0 1 23.552-24.384z m166.624-197.824c-20.64-26.048-36.544-31.616-52.064-25.6-13.44 5.216-27.392 19.2-39.36 37.344-12.832 19.488-38.784 24.48-58.816 13.152l-4.544-2.336c-21.12-9.696-40.384-3.296-59.744 15.264l-3.072 3.072-1.696 1.856-1.152 1.344 2.464 1.312c39.488 19.744 76.992 28.608 109.056 26.048l3.264-0.32c32.96-4.16 56.896-23.328 63.008-53.024l0.544-3.072a56.32 56.32 0 0 0-12.8-9.824l-3.712-1.984c-2.88-1.6-5.952-3.328-9.152-5.248l2.112-2.048c20.864-20.032 43.584-25.536 62.4-14.272 6.368 3.68 12.032 8.768 17.376 15.68z m79.552-64.64c-6.336-3.68-10.56-9.408-12.992-17.28l-0.64-2.304 3.456 1.664c6.464 3.136 10.24 8.256 11.456 14.72l0.384 2.88-1.664 0.32z"/>
              </svg>
            </button>
          </div>
        </div>

        ${this._renderWeekdayTabs()}
        ${this._config.show_timeline ? this._renderTimeline(timeline) : ''}
        ${this._config.show_timeline ? this._renderAddPlanButton() : ''}
        ${this._config.show_summary ? this._renderSummary(summary) : ''}
      </ha-card>
    `;
  }

  private _emptySummary(): TodaySummary {
    return {
      planAmount: 0,
      actualAmount: 0,
      manualAmount: 0,
      isOnline: false,
      totalCount: 0,
      completedCount: 0,
      pendingCount: 0,
    };
  }

  private _renderWeekdayTabs() {
    const today = getTodayWeekdayNumber();
    
    return html`
      <div class="weekday-tabs">
        ${[1, 2, 3, 4, 5, 6, 7].map(day => html`
          <button 
            class="weekday-tab ${this._selectedDay === day ? 'active' : ''} ${day === today ? 'today' : ''}"
            @click=${() => this._handleDaySwitch(day)}
          >
            ${WEEKDAY_NAMES[day]}
          </button>
        `)}
      </div>
    `;
  }

  private _handleDaySwitch(day: number): void {
    if (this._selectedDay !== day) {
      this._selectedDay = day;
      this._cancelEdit();
      this.requestUpdate();
    }
  }

  private _getDateDisplay(): string {
    const today = new Date();
    const currentWeekday = today.getDay(); // 0=周日, 1=周一...
    const currentWeekdayNum = currentWeekday === 0 ? 7 : currentWeekday; // 转为 1=周一...7=周日
    
    // 计算选中周天对应的日期
    const daysDiff = this._selectedDay - currentWeekdayNum;
    const targetDate = new Date(today);
    targetDate.setDate(today.getDate() + daysDiff);
    
    const month = targetDate.getMonth() + 1;
    const day = targetDate.getDate();
    const weekday = WEEKDAY_NAMES[this._selectedDay];
    return `${month}月${day}日 ${weekday}`;
  }

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
          ${timeline.map(item => this._renderTimelineItem(item))}
        </div>
      </div>
    `;
  }

  private _renderTimelineItem(item: TimelineItem) {
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

    const today = getTodayWeekdayNumber();
    const isToday = this._selectedDay === today;
    const isPast = this._selectedDay < today;  // 过去的日子
    
    // 判断是否已过期
    // - 过去的周天：所有计划都过期
    // - 今天：时间已过的计划过期
    // - 未来：都不过期
    let isExpired = false;
    if (isPast) {
      isExpired = true;
    } else if (isToday && item.time) {
      const now = new Date();
      const currentMinutes = now.getHours() * 60 + now.getMinutes();
      const [hours, minutes] = item.time.split(':').map(Number);
      const planMinutes = hours * 60 + minutes;
      isExpired = planMinutes < currentMinutes;
    }
    
    const canToggle = item.itemType === 'plan' && item.canDisable && !isExpired;
    const canDeleteBtn = item.itemType === 'plan' && item.canDelete;
    const canEdit = item.itemType === 'plan';

    const timeEl = editField === 'time' && this._editingItem
      ? html`
          <input 
            id="edit-time-${item.itemId}"
            type="time" 
            class="edit-time" 
            .value=${this._editingItem.time}
            @change=${(e: Event) => { if (this._editingItem) this._editingItem.time = (e.target as HTMLInputElement).value; }}
            @keydown=${(e: KeyboardEvent) => { if (e.key === 'Escape') this._cancelEdit(); }}
          />
        `
      : html`<span class="time ${canEdit ? 'editable' : ''}" @click=${canEdit ? () => this._startEdit(item, 'time') : undefined}>${item.time}</span>`;

    const nameEl = editField === 'name' && this._editingItem
      ? html`
          <input 
            id="edit-name-${item.itemId}"
            type="text" 
            class="edit-name" 
            .value=${this._editingItem.name}
            @change=${(e: Event) => { if (this._editingItem) this._editingItem.name = (e.target as HTMLInputElement).value; }}
            @keydown=${(e: KeyboardEvent) => { if (e.key === 'Escape') this._cancelEdit(); }}
            placeholder="名称"
          />
        `
      : html`<span class="name ${canEdit ? 'editable' : ''}" @click=${canEdit ? () => this._startEdit(item, 'name') : undefined}>${item.name}</span>`;

    const amount = item.actualAmount !== undefined ? item.actualAmount : item.plannedAmount;
    const amountEl = editField === 'amount' && this._editingItem
      ? html`
          <input 
            id="edit-amount-${item.itemId}"
            type="number" 
            class="edit-amount" 
            .value=${String(this._editingItem.amount)}
            min="1" max="100"
            @change=${(e: Event) => { if (this._editingItem) this._editingItem.amount = parseInt((e.target as HTMLInputElement).value) || 10; }}
            @keydown=${(e: KeyboardEvent) => { if (e.key === 'Escape') this._cancelEdit(); }}
          />
        `
      : html`<span class="amount ${canEdit ? 'editable' : ''}" @click=${canEdit ? () => this._startEdit(item, 'amount') : undefined}>${amount}g</span>`;

    return html`
      <div class="timeline-item ${item.itemType} ${editField ? 'editing' : ''} ${item.itemType === 'deleted_plan' ? 'plan-deleted' : ''}">
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
                    @click=${canToggle ? () => this._handleToggle(item) : undefined}
                    title="${item.itemType === 'deleted_plan' ? '已删除计划' : (isExpired ? '已过期' : (item.isExecuted ? '已执行' : (item.isEnabled ? '点击禁用' : '点击启用')))}"
                  >
                    <div class="toggle-thumb"></div>
                  </div>
                  <button 
                    class="icon-delete-btn ${!canDeleteBtn ? 'disabled' : ''}" 
                    @click=${canDeleteBtn ? () => this._handleDelete(item) : undefined}
                    title="${item.itemType === 'deleted_plan' ? '已删除计划' : '删除计划'}"
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

  private _renderAddPlanButton() {
    return html`
      <div class="timeline-list-footer">
        <button class="add-plan-btn" @click=${this._handleAddPlan} title="新增计划">
          <span class="add-plus"></span>
        </button>
      </div>
    `;
  }

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

  private async _handleManualFeed(): Promise<void> {
    if (!this.hass || !this._config) return;

    const feedEntity = this._getManualFeedEntity();
    if (feedEntity) {
      try {
        await this.hass.callService('button', 'press', { entity_id: feedEntity });
      } catch (error) {
        console.error('[PetkitFeeder] 手动喂食失败:', error);
      }
    }
  }

  private _getManualFeedEntity(): string | null {
    if (this.hass) {
      for (const entityId in this.hass.states) {
        if (entityId.startsWith('button.') && entityId.includes('petkit')) {
          const state = this.hass.states[entityId];
          const friendlyName = state?.attributes?.friendly_name || '';
          if (friendlyName.includes('手动') || friendlyName.includes('出粮') || friendlyName.toLowerCase().includes('feed')) {
            if (!friendlyName.includes('刷新') && !friendlyName.toLowerCase().includes('refresh')) {
              return entityId;
            }
          }
        }
      }
    }
    return null;
  }

  private async _handleRefresh(): Promise<void> {
    if (!this.hass || !this._config) return;

    const refreshEntity = this._getRefreshEntity();
    if (refreshEntity) {
      try {
        await this.hass.callService('button', 'press', { entity_id: refreshEntity });
      } catch (error) {
        console.error('[PetkitFeeder] 刷新失败:', error);
      }
    }
  }

  private _getRefreshEntity(): string | null {
    if (this._config?.refresh_entity) return this._config.refresh_entity;

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

  private async _handleToggle(item: TimelineItem): Promise<void> {
    if (!this.hass || !this._config) return;
    if (item.isExecuted) return;

    await toggleFeedingItem(
      this.hass,
      this._selectedDay,
      item,
      this._weeklyCache,
      () => this.requestUpdate(),
      (error) => {
        console.error('[PetkitFeeder] 切换失败:', error);
        this.requestUpdate();
      }
    );
  }

  private _handleDelete(item: TimelineItem): void {
    if (!this.hass || !this._config) return;

    // 从缓存中移除该项
    const dayCache = this._weeklyCache.getDayCache(this._selectedDay);
    if (dayCache) {
      dayCache.timeline = dayCache.timeline.filter(t => t.itemId !== item.itemId);
    }
    this.requestUpdate();

    // 如果正在保存中，不启动新的保存（变更已在缓存中，下次保存时会包含）
    if (this._isSaving) {
      console.log('[PetkitFeeder] 正在保存中，删除操作将在下次保存时生效');
      return;
    }

    // 统一使用 _saveDebounceTimer，防抖 2 秒后保存
    if (this._saveDebounceTimer) {
      clearTimeout(this._saveDebounceTimer);
    }

    console.log('[PetkitFeeder] 删除计划，启动防抖保存 (2000ms)');
    this._saveDebounceTimer = window.setTimeout(() => {
      this._saveDebounceTimer = null;
      this._triggerSave();
    }, 2000);
  }

  private _handleAddPlan(): void {
    if (!this.hass || !this._config) return;

    // 清除之前的防抖保存，确保新增不触发保存
    if (this._saveDebounceTimer) {
      clearTimeout(this._saveDebounceTimer);
      this._saveDebounceTimer = null;
    }

    // 标记正在添加新计划，防止 focusout 触发保存
    this._isAddingNewPlan = true;

    const newItemId = `new_${Date.now()}`;
    const newItem: TimelineItem = {
      id: newItemId,
      itemId: newItemId,
      time: '08:00',
      name: '早餐',
      timeSeconds: 8 * 3600,
      itemType: 'plan',
      plannedAmount: 10,
      isExecuted: false,
      isEnabled: true,
      canDisable: true,
      canDelete: true,
    };

    // 添加到缓存
    const dayCache = this._weeklyCache.getDayCache(this._selectedDay);
    if (dayCache) {
      dayCache.timeline.push(newItem);
      dayCache.timeline.sort((a, b) => a.time.localeCompare(b.time));
    }

    this._editingItem = {
      itemId: newItemId,
      field: 'name',
      time: '08:00',
      name: '早餐',
      amount: 10,
    };

    this._originalItemData = {
      time: '08:00',
      name: '早餐',
      amount: 10,
    };

    // 标记需要聚焦的输入框，updated 生命周期会处理
    this._pendingFocus = { itemId: newItemId, field: 'name' };
    this.requestUpdate();
  }

  private _startEdit(item: TimelineItem, field: 'time' | 'name' | 'amount'): void {
    // 取消之前的防抖保存
    if (this._saveDebounceTimer) {
      clearTimeout(this._saveDebounceTimer);
      this._saveDebounceTimer = null;
    }
    
    // 如果正在编辑另一个字段，先完成它（只更新缓存，不触发保存）
    if (this._editingItem && this._editingItem.itemId !== item.itemId) {
      this._finishEditSilent();
    }
    
    this._editingItem = {
      itemId: item.itemId,
      field: field,
      time: item.time,
      name: item.name,
      amount: item.plannedAmount,
    };

    this._originalItemData = {
      time: item.time,
      name: item.name,
      amount: item.plannedAmount,
    };

    // 标记正在进入编辑状态，防止 focusout 触发保存
    this._isAddingNewPlan = true;
    
    // 标记需要聚焦的输入框，updated 生命周期会处理
    this._pendingFocus = { itemId: item.itemId, field: field };
    this.requestUpdate();
  }

  private _finishEditSilent(): void {
    if (!this._editingItem || !this._originalItemData) return;

    const { itemId, time, name, amount } = this._editingItem;
    const hasChanges = time !== this._originalItemData.time ||
                       name !== this._originalItemData.name ||
                       amount !== this._originalItemData.amount;

    if (hasChanges) {
      const dayCache = this._weeklyCache.getDayCache(this._selectedDay);
      if (dayCache) {
        const item = dayCache.timeline.find(t => t.itemId === itemId);
        if (item) {
          item.time = time;
          item.name = name;
          item.plannedAmount = amount;
          
          const [h, m] = time.split(':').map(Number);
          item.timeSeconds = h * 3600 + m * 60;
          
          dayCache.timeline.sort((a, b) => a.time.localeCompare(b.time));
        }
      }
    }

    this._editingItem = null;
    this._originalItemData = null;
  }

  private _cancelEdit(): void {
    this._editingItem = null;
    this._originalItemData = null;
    if (this._saveDebounceTimer) {
      clearTimeout(this._saveDebounceTimer);
      this._saveDebounceTimer = null;
    }
    this.requestUpdate();
  }

  private _handleCardFocusOut(e: FocusEvent): void {
    // 如果正在添加新计划，忽略 focusout 事件
    if (this._isAddingNewPlan) {
      return;
    }
    
    // 检查是否有编辑输入框获得焦点
    const activeEl = document.activeElement;
    const isEditingInput = activeEl && (
      activeEl.classList.contains('edit-time') ||
      activeEl.classList.contains('edit-name') ||
      activeEl.classList.contains('edit-amount')
    );
    
    // 如果仍有编辑输入框获得焦点，不触发保存（正在切换编辑字段）
    if (isEditingInput) {
      // 完成当前编辑，写入缓存
      if (this._editingItem) {
        this._finishEditSilent();
        this.requestUpdate();  // 更新 UI，退出编辑状态
      }
      return;
    }
    
    // 检查焦点是否仍在卡片内
    const relatedTarget = e.relatedTarget as Element;
    const focusStillInCard = relatedTarget && this.contains(relatedTarget);
    
    if (focusStillInCard) {
      // 焦点仍在卡片内（点击了其他按钮等），完成编辑但不触发保存
      if (this._editingItem) {
        this._finishEditSilent();
        this.requestUpdate();  // 更新 UI，退出编辑状态
      }
      return;
    }

    // 焦点离开卡片：完成编辑并触发防抖保存
    if (this._editingItem) {
      this._finishEditSilent();
      this.requestUpdate();  // 更新 UI，退出编辑状态
    }

    // 如果正在保存中，不启动新的保存
    if (this._isSaving) {
      console.log('[PetkitFeeder] 正在保存中，跳过新的保存请求');
      return;
    }

    // 防抖保存
    if (this._saveDebounceTimer) {
      clearTimeout(this._saveDebounceTimer);
    }

    console.log('[PetkitFeeder] 焦点离开卡片，启动防抖保存 (1000ms)');
    this._saveDebounceTimer = window.setTimeout(() => {
      this._saveDebounceTimer = null;
      this._triggerSave();
    }, 1000);
  }

  private async _triggerSave(): Promise<void> {
    if (!this.hass || !this._config) return;
    
    // 防止重复保存
    if (this._isSaving) {
      console.log('[PetkitFeeder] 正在保存中，跳过重复调用');
      return;
    }

    const changedDays = this._weeklyCache.detectChanges();
    if (changedDays.length === 0) return;

    this._isSaving = true;
    console.log('[PetkitFeeder] 检测到变更，准备保存:', changedDays);

    try {
      await saveFeed(
        this.hass,
        changedDays,
        this._weeklyCache,
        () => {
          console.log('[PetkitFeeder] 保存成功');
          this.requestUpdate();
        },
        (error) => {
          console.error('[PetkitFeeder] 保存失败:', error);
          this.requestUpdate();
        }
      );
    } finally {
      this._isSaving = false;
    }
  }

  static styles = combineStyles();
}

if (!customElements.get('petkit-feeder-card')) {
  customElements.define('petkit-feeder-card', PetkitFeederCard);
}