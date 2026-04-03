/** 基础样式 */

import { css } from 'lit';

export const baseStyles = css`
  :host {
    display: block;
  }
  
  ha-card {
    padding: 10px;
  }
  
  /* 区块 */
  .section {
    margin-bottom: 8px;
  }

  /* 周天切换栏 */
  .weekday-tabs {
    display: flex;
    gap: 4px;
    padding: 3px 0;
    margin-bottom: 3px;
    border-bottom: 1px solid var(--divider-color, #e0e0e0);
  }

  .weekday-tab {
    flex: 1;
    height: 30px;
    padding: 0 4px;
    border: 2px solid transparent;
    border-radius: 4px;
    background: transparent;
    color: var(--secondary-text-color, #757575);
    font-size: 12px;
    cursor: pointer;
    transition: all 0.2s ease;
    box-sizing: border-box;
    display: flex;
    align-items: center;
    justify-content: center;
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

  /* 今天项：绘制空心框（当选中项不是今天时） */
  .weekday-tab.today:not(.active) {
    border-color: var(--primary-color, #03a9f4);
  }
`;