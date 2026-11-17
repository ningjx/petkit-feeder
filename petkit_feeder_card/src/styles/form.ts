/** 表单样式 */

import { css } from 'lit';

export const FORM_STYLES = css`
  .edit-time, .edit-name, .edit-amount {
    font-size: 14px;
    font-family: inherit;
    padding: 0px 0px;
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
    text-align: left;
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
    padding: 0px 0px;
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
    padding: 0px 0px;
    text-align: center;
  }
`;