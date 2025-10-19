from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from config import settings


DATABASE_URL = settings.get_db_url()

engine = create_async_engine(url=DATABASE_URL)

async_session_maker = async_sessionmaker(engine, expire_on_commit=False, echo=True)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with async_session_maker() as session:
        async with session.begin():
            yield session