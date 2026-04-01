/** 小佩喂食器卡片 - 入口文件 */

// 注册到卡片选择器
(window as any).customCards = (window as any).customCards || [];
(window as any).customCards.push({
  type: 'petkit-feeder-card',
  name: '小佩喂食器',
  description: '显示小佩喂食器状态、喂食计划和历史记录',
  preview: true,
  documentationURL: 'https://github.com/ning/petkit-ha',
});

// 导出组件
export { PetkitFeederCard } from './petkit-feeder-card';
export { PetkitFeederCardEditor } from './editor';
export type { PetkitSoloCardConfig, TimelineItem, TodaySummary } from './types';