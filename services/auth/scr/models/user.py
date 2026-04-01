import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Table, Column, String, DateTime, func, BigInteger
from sqlalchemy.orm import declarative_base

Base = declarative_base()

users = Table(
    "users",
    Base.metadata,

    Column("id",         UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("account_id",      BigInteger, nullable=False, unique=True, index=True),
    Column("hashed_password", String(255), nullable=False),

    # Временные метки — server_default делает это на уровне БД,
    # не Python, что гарантирует консистентность при bulk-insert
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column("updated_at", DateTime(timezone=True), server_default=func.now(),
           onupdate=func.now(), nullable=False),
    schema="users"
)