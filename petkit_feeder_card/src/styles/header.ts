/** 头部样式 */

import { css } from 'lit';

export const headerStyles = css`
  /* 头部 */
  .header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
    padding-bottom: 6px;
    border-bottom: 1px solid var(--divider-color);
    position: relative;
  }
  
  .header-title {
    font-size: 14px;
    font-weight: bold;
    z-index: 1;
  }
  
  .header-date {
    font-size: 12px;
    font-weight: bold;
    color: var(--secondary-text-color);
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
  }
  
  .header-actions {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-left: auto;
    z-index: 1;
  }
`;