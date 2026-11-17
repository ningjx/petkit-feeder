/** 卡片编辑器 - 可视化配置界面 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import { PetkitSoloCardConfig } from './types';
import { localize, getLanguage } from './localize';

@customElement('petkit-feeder-card-editor')
export class PetkitFeederCardEditor extends LitElement {
  @property() public hass?: any;
  @property() public config?: PetkitSoloCardConfig;

  private _schema = [
    { 
      name: 'device_id', 
      required: false, 
      selector: { text: {} },
      label: 'editor.device_id'
    },
    { 
      name: 'entity', 
      required: false, 
      selector: { entity: { domain: ['sensor'] } },
      label: 'editor.entity'
    },
    { 
      name: 'history_entity', 
      required: false, 
      selector: { entity: { domain: ['sensor'] } },
      label: 'editor.history_entity'
    },
    { 
      name: 'name', 
      selector: { text: {} },
      label: 'editor.card_title'
    },
    {
      type: 'grid',
      name: '',
      title: 'editor.display_control',
      schema: [
        { 
          name: 'show_timeline', 
          selector: { boolean: {} },
          label: 'editor.show_timeline'
        },
        { 
          name: 'show_summary', 
          selector: { boolean: {} },
          label: 'editor.show_summary'
        },
        { 
          name: 'show_actions', 
          selector: { boolean: {} },
          label: 'editor.show_actions'
        },
      ],
    },
  ];

  protected render() {
    if (!this.hass || !this.config) {
      return html`<div>${this._localize('common.loading_editor')}</div>`;
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
    return this._localize(schema.name || schema.label || schema.title);
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

  private _localize(key: string): string {
    const lang = getLanguage(this.hass || {});
    return localize(key, lang);
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
if (!customElements.get('petkit-feeder-card-editor')) {
  customElements.define('petkit-feeder-card-editor', PetkitFeederCardEditor);
}
