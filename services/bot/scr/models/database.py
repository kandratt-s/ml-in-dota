from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, String, DateTime, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "bot"}
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    token: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )


class DatabaseManager:
    def __init__(self, database_url: str):
        self.engine = create_async_engine(database_url, echo=False)
        self.session_factory = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    @asynccontextmanager
    async def get_session(self) -> AsyncSession:
        """Get database session as async context manager"""
        async with self.session_factory() as session:
            yield session

    async def close(self):
        """Close database engine"""
        await self.engine.dispose()


# Global database manager instance
db_manager: Optional[DatabaseManager] = None


def init_database(database_url: str) -> DatabaseManager:
    """Initialize database manager"""
    global db_manager
    db_manager = DatabaseManager(database_url)
    return db_manager


def get_db_manager() -> DatabaseManager:
    """Get current database manager"""
    if db_manager is None:
        raise RuntimeError("Database not initialized. Call init_database first.")
    return db_manager