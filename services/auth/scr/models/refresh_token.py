import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Table, Column, String, Boolean, DateTime, ForeignKey, func
from .user import Base


refresh_tokens = Table(
    "refresh_tokens",
    Base.metadata,

    Column("id",         UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("user_id",    UUID(as_uuid=True),
           ForeignKey("users.users.id", ondelete="CASCADE"), nullable=False, index=True),

    # Сам токен не хранится — только его хэш (SHA-256).
    # Если БД утечёт, токены нельзя будет использовать напрямую.
    Column("token_hash", String(64), nullable=False, unique=True),

    # jti — JWT ID, уникальный идентификатор из payload токена.
    # Нужен для быстрого поиска при rotation без декодирования JWT.
    Column("jti",        String(36), nullable=False, unique=True, index=True),

    Column("expires_at", DateTime(timezone=True), nullable=False),
    Column("revoked",    Boolean, nullable=False, server_default="false"),

    # Фингерпринт устройства — User-Agent + IP, хэшированные.
    # Позволяет обнаружить кражу токена: новый устройство = алерт.
    Column("fingerprint", String(64), nullable=True),

    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    schema="users",
)