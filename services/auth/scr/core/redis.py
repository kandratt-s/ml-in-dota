from redis.asyncio import Redis, ConnectionPool
from typing import AsyncGenerator

from .config import settings


# Пул соединений создаётся один раз при старте
_pool: ConnectionPool | None = None


def create_redis_pool() -> ConnectionPool:
    return ConnectionPool.from_url(
        str(settings.redis_url),
        max_connections=20,
        decode_responses=True,   # возвращает str, а не bytes
    )


def get_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        _pool = create_redis_pool()
    return _pool


async def get_redis() -> AsyncGenerator[Redis, None]:
    """FastAPI Dependency."""
    async with Redis(connection_pool=get_pool()) as redis:
        yield redis


async def close_redis_pool() -> None:
    global _pool
    if _pool:
        await _pool.disconnect()
        _pool = None