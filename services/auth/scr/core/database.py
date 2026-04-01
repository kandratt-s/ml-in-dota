from sqlalchemy.ext.asyncio import create_async_engine, AsyncConnection, AsyncEngine
from sqlalchemy import text
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from .config import settings
from scr.models.user import Base
import scr.models.refresh_token  # noqa: F401  # ensure table metadata is registered


def build_engine() -> AsyncEngine:
    return create_async_engine(
        str(settings.DATABASE_URL),
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        # pool_pre_ping проверяет соединение перед выдачей 
        # защита от "stale connection" после перезапуска БД
        pool_pre_ping=True,
    )


engine = build_engine()


async def init_db() -> None:
    """Create required schema and tables if they don't exist."""
    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS users"))
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def get_connection() -> AsyncGenerator[AsyncConnection, None]:
    """
    Контекст-менеджер соединения с автоматическим commit/rollback.
    Используется напрямую в сервисах для транзакций.
    """
    async with engine.begin() as conn:
        try:
            yield conn
        except Exception:
            await conn.rollback()
            raise


async def get_conn() -> AsyncGenerator[AsyncConnection, None]:
    """
    FastAPI Dependency версия. Используется через Depends().
    engine.begin() автоматически делает commit при выходе без ошибок
    и rollback при исключении.
    """
    async with engine.begin() as conn:
        yield conn