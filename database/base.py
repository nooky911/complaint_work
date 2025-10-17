from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from config import settings

DATABASE_URL = settings.get_db_url()

engine = create_async_engine(url=DATABASE_URL)

async_session_maker = async_sessionmaker(engine, expire_on_commit=False, echo=True)

class Base(DeclarativeBase):
    pass

# Декоратор для автоматического открытия и закрытия сессий
def db_session(method):
    async def wrapper(*args, **kwargs):
        async with async_session_maker() as session:
            async with session.begin():
                return await method(*args, session=session, **kwargs)
    return wrapper