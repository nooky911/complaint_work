"""Срок блокировки продлевается открытой формой редактирования"""

from datetime import datetime, timedelta, timezone

CASE_LOCK_TTL = timedelta(minutes=2)


def lock_expires_at(locked_at):
    if locked_at is None:
        return None
    if locked_at.tzinfo is None:
        locked_at = locked_at.replace(tzinfo=timezone.utc)
    return locked_at + CASE_LOCK_TTL


def is_case_lock_active(case, now=None):
    expires = lock_expires_at(case.locked_at)
    return bool(
        case.locked_by_id and expires and expires > (now or datetime.now(timezone.utc))
    )
