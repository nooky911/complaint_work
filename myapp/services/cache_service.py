import asyncio
import time
from typing import Any, Dict, Optional
from functools import wraps
from sqlalchemy.ext.asyncio import AsyncSession


class SimpleCache:
    """in-memory кеш для статических данных"""

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """Получить значение из кеша"""
        async with self._lock:
            if key in self._cache:
                item = self._cache[key]
                if time.time() < item["expires"]:
                    return item["value"]
                else:
                    del self._cache[key]
            return None

    async def set(self, key: str, value: Any, ttl_seconds: int = 300):
        """Сохранить значение в кеш"""
        async with self._lock:
            self._cache[key] = {"value": value, "expires": time.time() + ttl_seconds}

    async def clear(self):
        """Очистить кеш"""
        async with self._lock:
            self._cache.clear()

    async def delete(self, key: str):
        """Удалить конкретный ключ из кэша"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]


# Глобальный экземпляр кеша
cache = SimpleCache()


def cached(ttl_seconds: int = 300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            filterable_args = []
            for arg in args:
                if not isinstance(arg, AsyncSession):
                    if hasattr(arg, "model_dump"):
                        filterable_args.append(arg.model_dump())
                    else:
                        filterable_args.append(arg)

            cache_key = f"{func.__name__}_{hash(str(filterable_args) + str(sorted(kwargs.items())))}"

            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl_seconds)
            return result

        return wrapper

    return decorator
