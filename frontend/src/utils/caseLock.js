/** Просроченная серверная аренда не должна блокировать кнопку редактирования. */
export const isCaseLockedByOther = (repairCase, userId, now = Date.now()) =>
  Boolean(
    repairCase?.locked_by_id &&
    repairCase.locked_by_id !== userId &&
    repairCase.lock_expires_at &&
    Date.parse(repairCase.lock_expires_at) > now,
  );
