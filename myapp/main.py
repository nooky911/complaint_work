# -*- coding: utf-8 -*-
import asyncio
import uvicorn
import logging
from contextlib import asynccontextmanager, suppress
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Any

from myapp.config import settings
from myapp.database.base import Base
from myapp.database.base import engine
from myapp.api import api_router
from scripts.openapi_fix import openapi_encoding_fix
from myapp.debug_logger import setup_debug_logging
from myapp.services.product_passport_scheduler import (
    run_product_passport_sync_scheduler,
)


# -ФУНКЦИЯ СОЗДАНИЯ ТАБЛИЦ -
async def create_db_and_tables() -> None:
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

    passport_sync_task = None
    if settings.OMEGA_SYNC_ENABLED:
        passport_sync_task = asyncio.create_task(run_product_passport_sync_scheduler())

    yield

    if passport_sync_task:
        passport_sync_task.cancel()
        with suppress(asyncio.CancelledError):
            await passport_sync_task

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
async def log_requests(request: Request, call_next) -> Any:
    print(f"Метод: {request.method}")
    print(f"URL: {request.url}")
    print(f"Заголовки: {dict(request.headers)}")

    response = await call_next(request)
    return response


# -MIDDLEWARE (CORS) -
# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
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
