/** 卡片编辑器 - 可视化配置界面 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import { PetkitSoloCardConfig } from './types';

@customElement('petkit-solo-card-editor')
export class PetkitSoloCardEditor extends LitElement {
  @property() public hass?: any;
  @property() public config?: PetkitSoloCardConfig;

  private _schema = [
    { 
      name: 'entity', 
      required: true, 
      selector: { entity: { domain: ['sensor'] } },
      label: '喂食计划实体'
    },
    { 
      name: 'history_entity', 
      required: false, 
      selector: { entity: { domain: ['sensor'] } },
      label: '历史记录实体'
    },
    { 
      name: 'device_name_entity', 
      required: false, 
      selector: { entity: { domain: ['sensor'] } },
      label: '设备名称实体'
    },
    { 
      name: 'name', 
      selector: { text: {} },
      label: '卡片标题'
    },
    {
      type: 'grid',
      name: '',
      title: '显示控制',
      schema: [
        { 
          name: 'show_timeline', 
          selector: { boolean: {} },
          label: '显示时间线'
        },
        { 
          name: 'show_summary', 
          selector: { boolean: {} },
          label: '显示统计'
        },
        { 
          name: 'show_actions', 
          selector: { boolean: {} },
          label: '显示操作按钮'
        },
      ],
    },
  ];

  protected render() {
    if (!this.hass || !this.config) {
      return html`<div>正在加载...</div>`;
    }

    return html`
      <ha-form
        .hass=${this.hass}
        .data=${this.config}
        .schema=${this._schema}
        .computeLabel=${this._computeLabel}
        @value-changed=${this._valueChanged}
      ></ha-form>
    `;
  }

  private _computeLabel = (schema: any) => {
    const labels: Record<string, string> = {
      entity: '喂食计划实体',
      history_entity: '历史记录实体',
      device_name_entity: '设备名称实体',
      name: '卡片标题',
      show_timeline: '显示时间线',
      show_summary: '显示统计',
      show_actions: '显示操作按钮',
    };
    return labels[schema.name] || schema.label || schema.name;
  };

  private _valueChanged(ev: CustomEvent) {
    const config = ev.detail.value;
    this.config = config;

    const event = new CustomEvent('config-changed', {
      detail: { config },
      bubbles: true,
      composed: true,
    });
    this.dispatchEvent(event);
  }

  static get styles() {
    return css`
      :host {
        display: block;
      }
      ha-form {
        margin-top: 16px;
      }
    `;
  }
}

// 显式注册自定义元素
if (!customElements.get('petkit-solo-card-editor')) {
  customElements.define('petkit-solo-card-editor', PetkitSoloCardEditor);
}
