/** 组件样式（时间线、按钮、统计、状态） */

import { css } from 'lit';

export const COMPONENT_STYLES = css`
  /* 时间线条目 */
  .timeline-list {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .timeline-item {
    border: 1px solid var(--divider-color);
    border-radius: 6px;
    padding: 6px 10px;
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
    font-size: 14px;
    color: var(--primary-color);
    flex-shrink: 0;
    width: 55px;
  }

  .name {
    font-size: 14px;
    color: var(--primary-text-color);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    flex: 1 1 auto;
    min-width: 14px;
  }

  .amount {
    font-weight: bold;
    font-size: 14px;
    color: var(--primary-text-color);
    flex-shrink: 0;
    width: 40px;
    text-align: center;
  }

  .status-icon {
    width: 16px;
    height: 16px;
    flex-shrink: 0;
  }

  .item-actions {
    display: flex;
    gap: 8px;
    align-items: center;
    justify-content: flex-end;
    flex-shrink: 0;
  }

  .time.editable, .name.editable, .amount.editable {
    cursor: pointer;
    border-radius: 4px;
    transition: background-color 0.2s;
  }

  .time.editable:hover, .name.editable:hover, .amount.editable:hover {
    background-color: var(--primary-color, #03a9f4);
    color: white;
  }

  .timeline-item.editing {
    background-color: rgba(3, 169, 244, 0.1);
    border: 1px solid var(--primary-color, #03a9f4);
  }

  .timeline-item.disabled {
    opacity: 0.5;
  }

  .timeline-item.plan-deleted {
    opacity: 0.4;
  }

  .timeline-item.plan-deleted .time,
  .timeline-item.plan-deleted .name,
  .timeline-item.plan-deleted .amount {
    color: var(--disabled-text-color, #9e9e9e);
  }

  .timeline-list-footer {
    margin-top: 4px;
    margin-bottom: 4px;
  }

  /* 统一图标按钮 */
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
    outline: 0px solid var(--primary-color, #03a9f4);
    outline-offset: 0px;
  }

  .icon-btn.disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .icon-btn.disabled:hover {
    transform: none;
  }

  .icon-btn.disabled:hover::before {
    opacity: 0;
  }

  .btn-svg {
    width: 18px;
    height: 18px;
    fill: currentColor;
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .refresh-btn {
    color: var(--primary-text-color, #212121);
  }

  .refresh-btn:hover::before {
    opacity: 0;
  }

  .refresh-btn:hover .btn-svg {
    transform: rotate(180deg);
  }

  .feed-btn {
    width: 36px;
    height: 36px;
    background: var(--primary-color, #03a9f4);
    color: white;
    box-shadow: 0 0 0 1px var(--primary-color, #03a9f4), 0 0 8px 2px var(--primary-color, #03a9f4);
  }

  .feed-btn::before {
    background: white;
  }

  .feed-btn:hover {
    box-shadow: 0 0 0 1px var(--primary-color, #03a9f4), 0 0 12px 3px var(--primary-color, #03a9f4);
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

  .add-plan-btn.disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .add-plan-btn.disabled:hover {
    transform: none;
    background: transparent;
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

  /* 删除按钮 */
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

  /* 开关 */
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

  /* Toggle 加载状态 */
  .toggle-switch.loading {
    pointer-events: none;  /* 加载中禁止点击 */
  }

  .toggle-switch.loading .toggle-thumb {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  /* spinner 颜色跟随开关状态 */
  .toggle-switch.loading.on .spinner-svg {
    color: var(--primary-color, #03a9f4);
  }

  .toggle-switch.loading.off .spinner-svg {
    color: var(--disabled-color, #bdbdbd);
  }

  .spinner-svg {
    width: 8px;
    height: 8px;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }

  /* 统计行 */
  .summary-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    align-items: center;
    padding: 4px 4px;
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
    font-size: 11px;
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