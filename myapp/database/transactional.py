from sqlalchemy.ext.asyncio import AsyncSession
from functools import wraps


def transactional(func):
    """Декоратор, который управляет транзакцией для асинхронного сервисного метода"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        if args and isinstance(args[0], AsyncSession):
            session: AsyncSession = args[0]
        else:
            raise RuntimeError("Неверный первый аргумент")

        try:
            result = await func(*args, **kwargs)

            await session.commit()
            return result

        except Exception as e:
            await session.rollback()
            raise

    return wrapper
