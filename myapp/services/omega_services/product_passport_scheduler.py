import asyncio
import logging
from datetime import datetime, timedelta

from myapp.train.services.passport_sync_service import sync_new_train_passports
from myapp.config import settings
from myapp.services.omega_services.product_passport_sync_service import (
    ProductPassportSyncService,
)


logger = logging.getLogger("uvicorn.error")


async def run_product_passport_sync_scheduler() -> None:
    """Проверяет новые паспорта при старте и затем раз в сутки"""
    reason = "старт приложения"
    while True:
        logger.info("Запуск синхронизации паспортов: %s", reason)
        try:
            result = await ProductPassportSyncService.sync_new_passports(
                insert_only=True
            )
            logger.info("Результат синхронизации паспортов: %s", result)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Не удалось выполнить синхронизацию паспортов")
        try:
            train_result = await sync_new_train_passports()
            logger.info("Результат синхронизации поездных паспортов: %s", train_result)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Не удалось выполнить синхронизацию поездных паспортов")
        delay = _seconds_until_next_run()
        next_run = datetime.now().astimezone() + timedelta(seconds=delay)
        logger.info("Следующая синхронизация паспортов: %s", next_run.isoformat())
        await asyncio.sleep(delay)
        reason = "ежедневное расписание"


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
