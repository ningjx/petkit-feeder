/** 基础样式（包含 host、卡片、周天切换、头部） */

import { css } from 'lit';

export const BASE_STYLES = css`
  :host {
    display: block;
  }

  ha-card {
    padding: 10px;
  }

  /* 区块 */
  .section {
    margin-bottom: 0px;
  }

  /* 周天切换栏 */
  .weekday-tabs {
    display: flex;
    gap: 2px;
    padding: 4px 0;
    margin-bottom: 4px;
    border-bottom: 1px solid var(--divider-color, #e0e0e0);
  }

  .weekday-tab {
    flex: 1;
    min-width: 0;
    height: 28px;
    padding: 0 2px;
    border: 2px solid transparent;
    border-radius: 4px;
    background: transparent;
    color: var(--secondary-text-color, #757575);
    font-size: 14px;
    cursor: pointer;
    transition: all 0.2s ease;
    box-sizing: border-box;
    display: flex;
    align-items: center;
    justify-content: center;
    white-space: nowrap;
  }

  .weekday-tab:hover {
    background: var(--card-background-color, #f5f5f5);
  }

  .weekday-tab.active {
    background: var(--primary-color, #03a9f4);
    border-color: var(--primary-color, #03a9f4);
    color: white;
    font-weight: 500;
  }

  .weekday-tab.today:not(.active) {
    border-color: var(--primary-color, #03a9f4);
  }

  /* 头部 */
  .header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 0px;
    padding-bottom: 4px;
    border-bottom: 1px solid var(--divider-color);
    position: relative;
  }

  .header-title {
    font-size: 15px;
    font-weight: bold;
    z-index: 1;
    position: relative;
  }

  .header-date {
    font-size: 14px;
    font-weight: bold;
    color: var(--secondary-text-color);
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
    z-index: 2;
    background: linear-gradient(
      to right,
      transparent 0%,
      var(--card-background-color, var(--card-background-color, var(--paper-card-background-color, #fff))) 2%,
      var(--card-background-color, var(--card-background-color, var(--paper-card-background-color, #fff))) 98%,
      transparent 100%
    );
    padding: 2px 12px;
    border-radius: 4px;
  }

  .header-actions {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-left: auto;
    z-index: 3;
  }

  /* 同步按钮与刷新按钮之间的间距 */
  .sync-btn {
    margin-right: -5px;  /* 调整与刷新按钮的间距为 1px (6px gap - 5px = 1px) */
  }
`;