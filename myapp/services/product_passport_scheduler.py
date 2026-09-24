import asyncio
import logging
from datetime import datetime, timedelta

from myapp.config import settings
from myapp.services.product_passport_sync_service import ProductPassportSyncService

logger = logging.getLogger(__name__)


async def run_product_passport_sync_scheduler() -> None:
    """Запускает синхронизацию при старте и затем раз в сутки"""
    while True:
        try:
            await ProductPassportSyncService.sync_new_passports()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Не удалось выполнить синхронизацию паспортов")

        await asyncio.sleep(_seconds_until_next_run())


def _seconds_until_next_run() -> float:
    """Считает время до следующего ежедневного запуска"""
    now = datetime.now().astimezone()
    next_run = now.replace(
        hour=settings.OMEGA_SYNC_HOUR,
        minute=settings.OMEGA_SYNC_MINUTE,
        second=0,
        microsecond=0,
    )
    if next_run <= now:
        next_run += timedelta(days=1)
    return max((next_run - now).total_seconds(), 1)
