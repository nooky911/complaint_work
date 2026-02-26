from sqlalchemy.ext.asyncio import AsyncSession
from functools import wraps
import logging

logger = logging.getLogger(__name__)


def transactional(func):
    """Декоратор управления транзакцией"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        session = kwargs.get("session")
        if not session:
            for arg in args:
                if isinstance(arg, AsyncSession):
                    session = arg
                    break

        if not session or not isinstance(session, AsyncSession):
            raise RuntimeError(f"Неверный аргумент сессии в {func.__name__}")

        try:
            result = await func(*args, **kwargs)
            await session.commit()
            return result
        except Exception as e:
            await session.rollback()
            logger.error(f"{func.__name__}: {e}")
            raise e

    return wrapper
