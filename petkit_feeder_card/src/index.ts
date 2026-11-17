/** Petkit Feeder Card - Entry file */

// Register to card selector
(window as any).customCards = (window as any).customCards || [];
(window as any).customCards.push({
  type: 'petkit-feeder-card',
  name: 'Petkit Feeder Card',
  description: 'Display Petkit feeder status, feeding schedule and history',
  preview: true,
  documentationURL: 'https://github.com/ningjx/petkit-feeder/blob/main/petkit_feeder_card/README.md',
});

// 导入组件（确保执行装饰器和自定义元素注册）
import './petkit-feeder-card';
import './editor';

// 导出组件
export { PetkitFeederCard } from './petkit-feeder-card';
export { PetkitFeederCardEditor } from './editor';
export type { PetkitSoloCardConfig, TimelineItem, TodaySummary } from './types';
