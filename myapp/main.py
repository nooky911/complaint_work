# -*- coding: utf-8 -*-
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from myapp.database.base import Base
from myapp.database.base import engine
from myapp.api import api_router
from openapi_fix import openapi_encoding_fix
from myapp.debug_logger import setup_debug_logging

from fastapi import Request
import logging


# -ФУНКЦИЯ СОЗДАНИЯ ТАБЛИЦ -
async def create_db_and_tables():
    """Создает все таблицы в базе данных на основе Base"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Таблица создана")
    except Exception as e:
        print(f"ОШИБКА: таблица БД не создана. Подробнее {e}")


# Контекстный менеджер
@asynccontextmanager
async def lifespan(_: FastAPI):
    print("Приложение запущено. Создание таблиц")
    await create_db_and_tables()

    yield

    print("Приложение завершает работу")


# - ИНИЦИАЛИЗАЦИЯ FASTAPI -
app = FastAPI(
    lifespan=lifespan,
    title="Complaint Management API",
    version="1.0.0",
    description="API для управления случаями неисправностей и рекламационной работой",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Принудительная установка кодировки
openapi_encoding_fix(app)


logging.basicConfig(level=logging.DEBUG)


# Middleware для логирования всех запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"Метод: {request.method}")
    print(f"URL: {request.url}")
    print(f"Заголовки: {dict(request.headers)}")

    response = await call_next(request)
    return response


# -MIDDLEWARE (CORS) -
# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

# Подключаем роуты
app.include_router(api_router)

setup_debug_logging()

if __name__ == "__main__":
    uvicorn.run(
        "myapp.main:app", host="0.0.0.0", port=8000, reload=True, log_level="debug"
    )
