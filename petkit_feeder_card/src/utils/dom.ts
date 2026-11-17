/** DOM 操作辅助函数 */

/**
 * 检查元素是否是编辑输入框
 */
export function isEditInput(element: Element | null): boolean {
  if (!element) return false;
  return (
    element.classList.contains('edit-time') ||
    element.classList.contains('edit-name') ||
    element.classList.contains('edit-amount')
  );
}