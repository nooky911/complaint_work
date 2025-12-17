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
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
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


# Обработчик ошибок валидации
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    body = await request.body()
    try:
        body_str = body.decode("utf-8")
    except:
        body_str = str(body)

    print(f"Ошибки: {exc.errors()}")
    print(f"Тело запроса: {body_str}")

    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "body": body_str,
        },
    )


# Middleware для логирования всех запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"Метод: {request.method}")
    print(f"URL: {request.url}")
    print(f"Заголовки: {dict(request.headers)}")

    body = await request.body()
    print(f"Тело запроса {body}")

    async def receive():
        return {"type": "http.request", "body": body}

    request._receive = receive

    response = await call_next(request)
    return response


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

setup_debug_logging()

if __name__ == "__main__":
    uvicorn.run(
        "myapp.main:app", host="0.0.0.0", port=8000, reload=True, log_level="debug"
    )
