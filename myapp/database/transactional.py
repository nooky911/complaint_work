from functools import wraps
import logging
from typing import Any, Callable
from sqlalchemy.ext.asyncio import AsyncSession


logger = logging.getLogger(__name__)


def transactional(func) -> Callable[..., Any]:
    """Декоратор управления транзакцией"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        """Сохраняет общую транзакцию после завершения всех вложенных операций"""
        session = kwargs.get("session")
        if not session:
            for arg in args:
                if isinstance(arg, AsyncSession):
                    session = arg
                    break

        if not session or not isinstance(session, AsyncSession):
            raise RuntimeError(f"Неверный аргумент сессии в {func.__name__}")

        depth = session.info.get("transactional_depth", 0)
        session.info["transactional_depth"] = depth + 1
        try:
            result = await func(*args, **kwargs)
            if depth == 0:
                await session.commit()
        except Exception:
            if depth == 0:
                session.info.pop("after_commit", None)
                await session.rollback()
                logger.exception("Ошибка транзакции в %s", func.__name__)
            raise
        finally:
            session.info["transactional_depth"] = depth

        if depth == 0:
            for callback in session.info.pop("after_commit", []):
                try:
                    await callback()
                except Exception:
                    # Данные уже сохранены, поэтому ошибку удаления файла записываем без отката
                    logger.exception(
                        "Не удалось удалить файл после сохранения изменений"
                    )
        return result

    return wrapper
