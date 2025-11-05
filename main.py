# -*- coding: utf-8 -*-
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from myapp.database.base import Base
from myapp.database.base import engine
from myapp.api import api_router
from openapi_fix import openapi_encoding_fix


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


# -MIDDLEWARE (CORS) -
# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ПОМЕНЯТЬ
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Подключаем роуты
app.include_router(api_router)


# если запускать как python main.py
if __name__ == "__main__":
    # Обычно запускается командой 'uvicorn main:app --reload', но это полезно для отладки
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
