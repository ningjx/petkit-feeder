/** 编辑事件处理 */

import { TimelineItem } from '../types';
import { PendingChange } from '../data';
import { EditField, EditingItem, OriginalItemData } from '../state';

/**
 * 开始编辑
 */
export function startEdit(
  item: TimelineItem,
  field: EditField,
  pendingChanges: Map<string, PendingChange>,
  currentTimeout: number | null,
  onClearTimeout: () => void,
  onSetEditState: (editing: EditingItem, original: OriginalItemData) => void,
  onRequestUpdate: () => void
): void {
  if (currentTimeout !== null) {
    onClearTimeout();
  }

  const pendingChange = pendingChanges.get(item.itemId);
  const editTime = pendingChange?.time || item.time;
  const editName = pendingChange?.name || item.name;
  const editAmount = pendingChange?.amount ?? item.plannedAmount;

  onSetEditState(
    {
      itemId: item.itemId,
      field: field,
      time: editTime,
      name: editName,
      amount: editAmount,
    },
    {
      time: editTime,
      name: editName,
      amount: editAmount,
    }
  );
  onRequestUpdate();
}

/**
 * 取消编辑
 */
export function cancelEdit(
  editingItemId: string | undefined,
  pendingChanges: Map<string, PendingChange>,
  currentTimeout: number | null,
  onClearTimeout: () => void,
  onClearEditState: () => void,
  onRequestUpdate: () => void
): void {
  if (editingItemId) {
    const pendingChange = pendingChanges.get(editingItemId);
    if (pendingChange?.isNew) {
      pendingChanges.delete(editingItemId);
    }
  }
  onClearEditState();
  if (currentTimeout !== null) {
    onClearTimeout();
  }
  onRequestUpdate();
}

/**
 * 新增计划
 */
export function addNewPlan(
  pendingChanges: Map<string, PendingChange>,
  currentTimeout: number | null,
  onClearTimeout: () => void,
  onSetEditState: (editing: EditingItem, original: OriginalItemData) => void,
  onRequestUpdate: () => void
): string {
  if (currentTimeout !== null) {
    onClearTimeout();
  }

  const newItemId = `new_${Date.now()}`;

  pendingChanges.set(newItemId, {
    time: '00:00',
    name: '早餐',
    amount: 10,
    isNew: true,
  });

  onSetEditState(
    {
      itemId: newItemId,
      field: 'name',
      time: '00:00',
      name: '早餐',
      amount: 10,
    },
    {
      time: '00:00',
      name: '早餐',
      amount: 10,
    }
  );

  console.log('[PetkitFeeder] 新增计划:', newItemId);
  onRequestUpdate();
  return newItemId;
}