/** 小佩喂食器卡片 - 主组件 */

import { LitElement, html } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import { HomeAssistant } from 'custom-card-helpers';
import { PetkitSoloCardConfig, TimelineItem, TodaySummary } from './types';
import { getEntityId, getTodayWeekdayNumber, getConnectivityEntityId, findManualFeedEntity, findRefreshEntity, isEditInput, REFRESH_ICON, FEED_ICON, STATUS_ICON, DELETE_ICON, SPINNER_ICON, SYNC_ICON, isItemExpired, getToggleTitle, getDateDisplay } from './utils';
import { processWeeklyData, getEmptySummary } from './data';
import { combineStyles } from './styles';
import { saveFeed, toggleFeedingItem, pressButton } from './services';
import { WeeklyCacheManager, EditState } from './state';
import { localize, getLanguage } from './localize';

@customElement('petkit-feeder-card')
export class PetkitFeederCard extends LitElement {
  /** ============================================================================
   * 属性定义
   * ============================================================================ */
  @property({ attribute: false }) public hass!: HomeAssistant;
  @property({ attribute: false }) private _config?: PetkitSoloCardConfig;

  // 数据与状态管理
  private _weeklyCache: WeeklyCacheManager = new WeeklyCacheManager();
  private _editState: EditState = new EditState();
  private _selectedDay: number = 1;
  private _isOnline: boolean = true;  // 设备在线状态

  // 保存相关状态
  private _saveDebounceTimer: number | null = null;
  private _isSaving: boolean = false;

  // 编辑相关状态
  private _pendingFocus: { itemId: string; field: 'time' | 'name' | 'amount' } | null = null;
  private _isInEditMode: boolean = false;  // 标记正在添加/编辑（用于阻止 focusout 保存）

  // Toggle 加载状态（支持并行操作多个开关）
  private _togglingItemIds: Set<string> = new Set();  // 正在切换的 item ID 集合

  private _getEntityId(entityType: string): string {
    if (!this._config) return '';
    return getEntityId(this._config, entityType);
  }

  /** ============================================================================
   * 生命周期与配置方法
   * ============================================================================ */
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
      throw new Error(localize('error.device_or_entity_required'));
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
      this._isInEditMode = false;
      this._pendingFocus = null;
    }
  }

  /** ============================================================================
   * 渲染方法
   * ============================================================================ */
  protected render() {
    if (!this._config || !this.hass) {
      return html`<div>${this._localize('common.loading')}</div>`;
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
            <p>${this._localize('error.entity_not_found', { entityId: planEntityId })}</p>
          </div>
        </ha-card>
      `;
    }

    // 读取在线状态
    const connectivityEntityId = getConnectivityEntityId(this._config);
    const connectivityEntity = this.hass.states[connectivityEntityId];
    const isOnline = connectivityEntity?.state === 'on';
    this._isOnline = isOnline;  // 存储到组件属性

    // 处理一周数据
    const language = getLanguage(this.hass);
    const weeklyData = processWeeklyData(
      planEntity.attributes,
      historyEntity?.attributes || {},
      isOnline,
      language
    );

    // 初始化或更新缓存
    if (!this._weeklyCache.originData) {
      this._weeklyCache.initOrigin(weeklyData);
      this._selectedDay = getTodayWeekdayNumber();
    }

    // 获取当前选中天的数据
    const dayData = this._weeklyCache.getDayCache(this._selectedDay);
    const timeline = dayData?.timeline || [];
    const summary = dayData?.summary || getEmptySummary();

    let deviceName = this._config.name;
    if (!deviceName) {
      const deviceNameEntityId = this._config.device_name_entity || this._getEntityId('device_name');
      const deviceNameEntity = this.hass.states[deviceNameEntityId];
      deviceName = deviceNameEntity?.state;
    }
    if (!deviceName) {
      deviceName = planEntity.attributes.friendly_name || this._localize('default.device_name');
    }

    return html`
      <ha-card @focusout=${this._handleCardFocusOut}>
        <div class="header">
          <span class="header-title">${deviceName}</span>
          <span class="header-date">${getDateDisplay(this._selectedDay, this._localize.bind(this))}</span>
          <div class="header-actions">
            <button
              class="icon-btn sync-btn ${!isOnline ? 'disabled' : ''}"
              @click=${isOnline ? this._handleSync : undefined}
              title="${isOnline ? this._localize('button.sync') : this._localize('status.offline')}"
              ?disabled=${!isOnline}
            >
              ${SYNC_ICON}
            </button>
            <button
              class="icon-btn refresh-btn"
              @click=${this._handleRefresh}
              title="${this._localize('button.refresh')}"
            >
              ${REFRESH_ICON}
            </button>
            <button
              class="icon-btn feed-btn ${!isOnline ? 'disabled' : ''}"
              @click=${isOnline ? this._handleManualFeed : undefined}
              title="${isOnline ? this._localize('button.manual_feed') : this._localize('status.offline')}"
              ?disabled=${!isOnline}
            >
              ${FEED_ICON}
            </button>
          </div>
        </div>

        ${this._renderWeekdayTabs()}
        ${this._config.show_timeline ? this._renderTimeline(timeline, this._isOnline) : ''}
        ${this._config.show_timeline ? this._renderAddPlanButton(this._isOnline) : ''}
        ${this._config.show_summary ? this._renderSummary(summary) : ''}
      </ha-card>
    `;
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
            ${this._localize(`weekday.${day}`)}
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

  private _renderTimeline(timeline: TimelineItem[], isOnline: boolean) {
    if (!timeline.length) {
      return html`
        <div class="section">
          <div class="empty-state">
            <ha-icon .icon=${'mdi:calendar-blank'}></ha-icon>
            <p>${this._localize('timeline.empty')}</p>
          </div>
        </div>
      `;
    }

    return html`
      <div class="section">
        <div class="timeline-list">
          ${timeline.map(item => this._renderTimelineItem(item, isOnline))}
        </div>
      </div>
    `;
  }

  /** 判断计划项是否已过期 */
  private _renderTimelineItem(item: TimelineItem, isOnline: boolean) {
    const editingItem = this._editState.editingItem;
    const editField = editingItem?.itemId === item.itemId ? editingItem?.field : null;
    const isExpired = isItemExpired(item, this._selectedDay);

    // 权限判断（离线时禁止所有操作）
    const canToggle = isOnline && item.itemType === 'plan' && item.canDisable && !isExpired;
    const canDeleteBtn = isOnline && item.itemType === 'plan' && item.canDelete;
    const canEdit = isOnline && item.itemType === 'plan';

    // 编辑输入框
    const timeEl = editField === 'time' && editingItem
      ? html`
          <input
            id="edit-time-${item.itemId}"
            type="time"
            class="edit-time"
            .value=${editingItem.time}
            @change=${(e: Event) => this._editState.updateEditData((e.target as HTMLInputElement).value)}
            @keydown=${(e: KeyboardEvent) => { if (e.key === 'Escape') this._cancelEdit(); }}
          />
        `
      : html`<span class="time ${canEdit ? 'editable' : ''}" @click=${canEdit ? () => this._startEdit(item, 'time') : undefined}>${item.time}</span>`;

    const nameEl = editField === 'name' && editingItem
      ? html`
          <input
            id="edit-name-${item.itemId}"
            type="text"
            class="edit-name"
            .value=${editingItem.name}
            @change=${(e: Event) => this._editState.updateEditData(undefined, (e.target as HTMLInputElement).value)}
            @keydown=${(e: KeyboardEvent) => { if (e.key === 'Escape') this._cancelEdit(); }}
            placeholder="${this._localize('placeholder.name')}"
          />
        `
      : html`<span class="name ${canEdit ? 'editable' : ''}" @click=${canEdit ? () => this._startEdit(item, 'name') : undefined}>${item.name}</span>`;

    const amount = item.actualAmount !== undefined ? item.actualAmount : item.plannedAmount;
    const amountEl = editField === 'amount' && editingItem
      ? html`
          <input
            id="edit-amount-${item.itemId}"
            type="number"
            class="edit-amount"
            .value=${String(editingItem.amount)}
            min="1" max="100"
            @change=${(e: Event) => this._editState.updateEditData(undefined, undefined, parseInt((e.target as HTMLInputElement).value) || 10)}
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
          ${STATUS_ICON(item.isExecuted)}
          <div class="item-actions">
            ${this._config?.show_actions
              ? html`
                  <div
                    class="toggle-switch ${item.isEnabled ? 'on' : 'off'} ${!canToggle ? 'disabled' : ''} ${this._togglingItemIds.has(item.itemId) ? 'loading' : ''}"
                    @click=${canToggle && !this._togglingItemIds.has(item.itemId) ? () => this._handleToggle(item) : undefined}
                    title="${getToggleTitle(item, isExpired, this._localize.bind(this))}"
                  >
                    <div class="toggle-thumb">
                      ${this._togglingItemIds.has(item.itemId) ? SPINNER_ICON : ''}
                    </div>
                  </div>
                  <button
                    class="icon-delete-btn ${!canDeleteBtn ? 'disabled' : ''}"
                    @click=${canDeleteBtn ? () => this._handleDelete(item) : undefined}
                    title="${item.itemType === 'deleted_plan' ? this._localize('status.deleted') : this._localize('button.delete_plan')}"
                    ?disabled=${!canDeleteBtn}
                  >
                    ${DELETE_ICON}
                  </button>
                `
              : ''}
          </div>
        </div>
      </div>
    `;
  }

  private _renderAddPlanButton(isOnline: boolean) {
    return html`
      <div class="timeline-list-footer">
        <button
          class="add-plan-btn ${!isOnline ? 'disabled' : ''}"
          @click=${isOnline ? this._handleAddPlan : undefined}
          title="${isOnline ? this._localize('button.add_plan') : this._localize('status.offline')}"
          ?disabled=${!isOnline}
        >
          <span class="add-plus"></span>
        </button>
      </div>
    `;
  }

  private _renderSummary(summary: TodaySummary) {
    return html`
      <div class="summary-row">
        <span class="summary-item">
          <span class="summary-label">${this._localize('summary.online_status')}</span>
          <span class="summary-value ${!summary.isOnline ? 'offline' : ''}">${summary.isOnline ? this._localize('status.online') : this._localize('status.offline')}</span>
        </span>
        <span class="summary-item">
          <span class="summary-label">${this._localize('summary.planned_feed')}</span>
          <span class="summary-value">${summary.planAmount}g</span>
        </span>
        <span class="summary-item">
          <span class="summary-label">${this._localize('summary.actual_feed')}</span>
          <span class="summary-value">${summary.actualAmount}g</span>
        </span>
        <span class="summary-item">
          <span class="summary-label">${this._localize('summary.manual_feed')}</span>
          <span class="summary-value">${summary.manualAmount}g</span>
        </span>
      </div>
    `;
  }

  /** ============================================================================
   * 事件处理方法
   * ============================================================================ */
  private async _handleManualFeed(): Promise<void> {
    if (!this.hass) return;
    if (!this._isOnline) return;  // 离线时禁止
    const feedEntity = findManualFeedEntity(this.hass);
    if (feedEntity) {
      await pressButton(this.hass, feedEntity, '手动喂食');
    }
  }

  private async _handleRefresh(): Promise<void> {
    if (!this.hass || !this._config) return;
    const refreshEntity = findRefreshEntity(this.hass, this._config.refresh_entity);
    if (refreshEntity) {
      await pressButton(this.hass, refreshEntity, '刷新');
    }
  }

  private async _handleSync(): Promise<void> {
    if (!this.hass || !this._config) return;
    if (!this._isOnline) return;

    // 1. 确认对话框（防止误操作）
    const confirmed = window.confirm(
      this._localize('confirm.sync_plan', { day: this._localize(`weekday.${this._selectedDay}`) })
    );
    if (!confirmed) return;

    // 2. 获取当前选中周天的计划数据
    const currentDayData = this._weeklyCache.getDayCache(this._selectedDay);
    if (!currentDayData) return;

    // 3. 提取计划项（仅 itemType === 'plan'）
    const planItems = currentDayData.timeline
      .filter(item => item.itemType === 'plan')
      .map(item => ({
        time: item.time,
        amount: item.plannedAmount,
        name: item.name,
        enabled: item.isEnabled,
      }));

    // 4. 构建所有 7 天的数据（全部使用当前周天的计划）
    for (let day = 1; day <= 7; day++) {
      const dayCache = this._weeklyCache.getDayCache(day);
      if (dayCache) {
        // 复制当前周天的计划项到其他天
        dayCache.timeline = currentDayData.timeline
          .filter(item => item.itemType === 'plan')
          .map(item => ({
            ...item,
            itemId: item.itemId.startsWith('new_')
              ? `new_${day}_${Date.now()}_${item.time.replace(':', '')}`
              : `s${day}${item.itemId.replace(/^s\d+/, '')}`,
          }));
      }
    }
    this.requestUpdate();

    // 5. 调用保存服务
    const weeklyPlan: Array<{ day: number; suspended: number; items: Array<{ time: string; amount: number; name: string; enabled: boolean }> }> = [];
    for (let day = 1; day <= 7; day++) {
      weeklyPlan.push({
        day,
        suspended: 0,
        items: planItems,
      });
    }

    try {
      await this.hass.callService('petkit_feeder', 'save_feed', {
        weekly_plan: weeklyPlan,
      });
      this._weeklyCache.commit();
      console.log('[PetkitFeeder] 同步计划成功');
    } catch (error) {
      console.error('[PetkitFeeder] 同步计划失败:', error);
      this._weeklyCache.rollback();
      this.requestUpdate();
      window.alert(this._localize('error.sync_failed'));
    }
  }

  private async _handleToggle(item: TimelineItem): Promise<void> {
    if (!this.hass || !this._config) return;
    if (!this._isOnline) return;  // 离线时禁止
    if (item.isExecuted) return;
    if (this._togglingItemIds.has(item.itemId)) return;  // 防止重复点击同一项

    // 1. 设置 loading 状态，立即刷新 UI 显示 spinner
    this._togglingItemIds.add(item.itemId);
    this.requestUpdate();  // 立即刷新，显示 spinner + 执行动画

    // 2. 调用后台服务（乐观更新已在 toggleFeedingItem 中实现）
    const result = await toggleFeedingItem(
      this.hass,
      this._selectedDay,
      item,
      this._weeklyCache
    );

    // 3. 清除 loading 状态
    this._togglingItemIds.delete(item.itemId);

    if (!result.success) {
      console.error('[PetkitFeeder] 切换失败:', result.error);
    }
    this.requestUpdate();
  }

  private _handleDelete(item: TimelineItem): void {
    if (!this.hass || !this._config) return;
    if (!this._isOnline) return;  // 离线时禁止

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
    this._clearSaveTimer();

    console.log('[PetkitFeeder] 删除计划，启动防抖保存 (5000ms)');
    this._saveDebounceTimer = window.setTimeout(() => {
      this._saveDebounceTimer = null;
      this._triggerSave();
    }, 5000);
  }

  private _handleAddPlan(): void {
    if (!this.hass || !this._config) return;
    if (!this._isOnline) return;  // 离线时禁止

    // 清除之前的防抖保存，确保新增不触发保存
    this._clearSaveTimer();

    // 标记正在添加新计划，防止 focusout 触发保存
    this._isInEditMode = true;

    const newItemId = `new_${Date.now()}`;
    const planName = this._localize('default.plan_name');
    const newItem: TimelineItem = {
      id: newItemId,
      itemId: newItemId,
      time: '08:00',
      name: planName,
      itemType: 'plan',
      plannedAmount: 10,
      isExecuted: false,
      isEnabled: true,
      canDisable: true,
      canDelete: true,
    };

    const dayCache = this._weeklyCache.getDayCache(this._selectedDay);
    if (dayCache) {
      dayCache.timeline.push(newItem);
      dayCache.timeline.sort((a, b) => a.time.localeCompare(b.time));
    }

    // 使用 EditState 开始编辑
    this._editState.startEdit(
      newItemId,
      'name',
      '08:00',
      planName,
      10,
      '08:00',
      planName,
      10
    );

    // 标记需要聚焦的输入框，updated 生命周期会处理
    this._pendingFocus = { itemId: newItemId, field: 'name' };
    this.requestUpdate();
  }

  /** ============================================================================
   * 编辑状态管理方法
   * ============================================================================ */
  private _startEdit(item: TimelineItem, field: 'time' | 'name' | 'amount'): void {
    if (!this._isOnline) return;  // 离线时禁止编辑

    // 取消之前的防抖保存
    this._clearSaveTimer();

    // 如果正在编辑另一个字段，先完成它（只更新缓存，不触发保存）
    if (this._editState.isEditing && this._editState.editingItem?.itemId !== item.itemId) {
      this._finishEditSilent();
    }

    // 使用 EditState 开始编辑
    this._editState.startEdit(
      item.itemId,
      field,
      item.time,
      item.name,
      item.plannedAmount,
      item.time,
      item.name,
      item.plannedAmount
    );

    // 标记正在进入编辑状态，防止 focusout 触发保存
    this._isInEditMode = true;

    // 标记需要聚焦的输入框，updated 生命周期会处理
    this._pendingFocus = { itemId: item.itemId, field: field };
    this.requestUpdate();
  }

  private _finishEditSilent(): void {
    const editingItem = this._editState.editingItem;
    const originalData = this._editState.originalItemData;
    if (!editingItem || !originalData) return;

    const { itemId, time, name, amount } = editingItem;
    const hasChanges = time !== originalData.time ||
                       name !== originalData.name ||
                       amount !== originalData.amount;

    if (hasChanges) {
      const dayCache = this._weeklyCache.getDayCache(this._selectedDay);
      if (dayCache) {
        const item = dayCache.timeline.find(t => t.itemId === itemId);
        if (item) {
          item.time = time;
          item.name = name;
          item.plannedAmount = amount;

          dayCache.timeline.sort((a, b) => a.time.localeCompare(b.time));
        }
      }
    }

    this._editState.completeEdit();
  }

  private _cancelEdit(): void {
    this._editState.cancelEdit();
    this._clearSaveTimer();
    this.requestUpdate();
  }

  private _clearSaveTimer(): void {
    if (this._saveDebounceTimer) {
      clearTimeout(this._saveDebounceTimer);
      this._saveDebounceTimer = null;
    }
  }

  private _handleCardFocusOut(e: FocusEvent): void {
    // 如果正在添加新计划或切换状态，忽略 focusout 事件
    if (this._isInEditMode || this._togglingItemIds.size > 0) {
      return;
    }

    // 检查是否有编辑输入框获得焦点（使用辅助函数）
    const activeEl = document.activeElement;
    if (isEditInput(activeEl)) {
      // 完成当前编辑，写入缓存
      if (this._editState.isEditing) {
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
      if (this._editState.isEditing) {
        this._finishEditSilent();
        this.requestUpdate();  // 更新 UI，退出编辑状态
      }
      return;
    }

    // 焦点离开卡片：完成编辑并触发防抖保存
    if (this._editState.isEditing) {
      this._finishEditSilent();
      this.requestUpdate();  // 更新 UI，退出编辑状态
    }

    // 如果正在保存中，不启动新的保存
    if (this._isSaving) {
      console.log('[PetkitFeeder] 正在保存中，跳过新的保存请求');
      return;
    }

    // 防抖保存
    this._clearSaveTimer();

    console.log('[PetkitFeeder] 焦点离开卡片，启动防抖保存 (1000ms)');
    this._saveDebounceTimer = window.setTimeout(() => {
      this._saveDebounceTimer = null;
      this._triggerSave();
    }, 1000);
  }

  /** ============================================================================
   * 保存逻辑方法
   * ============================================================================ */
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

    const result = await saveFeed(
      this.hass,
      changedDays,
      this._weeklyCache
    );

    this._isSaving = false;

    if (result.success) {
      console.log('[PetkitFeeder] 保存成功');
    } else {
      console.error('[PetkitFeeder] 保存失败:', result.error);
    }
    this.requestUpdate();
  }

  static styles = combineStyles();

  /** ============================================================================
   * 辅助方法
   * ============================================================================ */
  private _localize(key: string, params?: Record<string, string | number>): string {
    const lang = getLanguage(this.hass);
    return localize(key, lang, params);
  }
}

if (!customElements.get('petkit-feeder-card')) {
  customElements.define('petkit-feeder-card', PetkitFeederCard);
}