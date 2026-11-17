/** 样式汇总 */

import { css } from 'lit';
import { BASE_STYLES } from './base';
import { COMPONENT_STYLES } from './components';
import { FORM_STYLES } from './form';

/**
 * 合并所有样式
 */
export const combineStyles = () => css`
  ${BASE_STYLES}
  ${COMPONENT_STYLES}
  ${FORM_STYLES}
`;