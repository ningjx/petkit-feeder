/** 保存处理 */

import { PendingChange } from '../data';
import { EditingItem, OriginalItemData } from '../state';

/**
 * 检查是否有变更
 */
export function hasChanges(
  editData: EditingItem,
  originalData: OriginalItemData | null
): boolean {
  if (!originalData) return false;
  return (
    editData.time !== originalData.time ||
    editData.name !== originalData.name ||
    editData.amount !== originalData.amount
  );
}

/**
 * 准备保存数据
 */
export function prepareSaveData(
  editingItem: EditingItem,
  originalData: OriginalItemData | null,
  pendingChanges: Map<string, PendingChange>
): {
  editData: EditingItem;
  isNew: boolean;
  hasChanges: boolean;
} {
  const pendingChange = pendingChanges.get(editingItem.itemId);
  const isNew = pendingChange?.isNew === true;

  // 更新待提交变更
  pendingChanges.set(editingItem.itemId, {
    time: editingItem.time,
    name: editingItem.name,
    amount: editingItem.amount,
    isNew: isNew,
  });

  return {
    editData: { ...editingItem },
    isNew,
    hasChanges: hasChanges(editingItem, originalData),
  };
}