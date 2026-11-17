/** 编辑状态管理类 */

import { EditingItem, OriginalItemData, EditField } from '../types';

/**
 * 编辑状态管理类
 */
export class EditState {
  private _editingItem: EditingItem | null = null;
  private _originalItemData: OriginalItemData | null = null;

  /** 获取当前编辑项 */
  get editingItem(): EditingItem | null {
    return this._editingItem;
  }

  /** 获取原始数据 */
  get originalItemData(): OriginalItemData | null {
    return this._originalItemData;
  }

  /** 是否正在编辑 */
  get isEditing(): boolean {
    return this._editingItem !== null;
  }

  /** 开始编辑 */
  startEdit(
    itemId: string,
    field: EditField,
    time: string,
    name: string,
    amount: number,
    originalTime: string,
    originalName: string,
    originalAmount: number
  ): void {
    this._editingItem = { itemId, field, time, name, amount };
    this._originalItemData = { time: originalTime, name: originalName, amount: originalAmount };
  }

  /** 更新编辑数据 */
  updateEditData(time?: string, name?: string, amount?: number): void {
    if (this._editingItem) {
      if (time !== undefined) this._editingItem.time = time;
      if (name !== undefined) this._editingItem.name = name;
      if (amount !== undefined) this._editingItem.amount = amount;
    }
  }

  /** 取消编辑 */
  cancelEdit(): void {
    this._editingItem = null;
    this._originalItemData = null;
  }

  /** 完成编辑 */
  completeEdit(): void {
    this._editingItem = null;
    this._originalItemData = null;
  }
}