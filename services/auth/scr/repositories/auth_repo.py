import hashlib
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, insert, update, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncConnection

from scr.models.user import users
from scr.models.refresh_token import refresh_tokens
from scr.schemas.user import UserInDB
from scr.schemas.token import RefreshTokenCreate


class AuthRepository:
    """
    Репозиторий — единственное место, где живёт SQL.
    Сервисный слой не знает о таблицах и запросах.
    Все методы принимают conn: AsyncConnection —
    управление транзакцией остаётся на вызывающей стороне.
    """

    # ------------------------------------------------------------------ #
    #  Users                                                               #
    # ------------------------------------------------------------------ #

    async def create_user(
        self,
        conn: AsyncConnection,
        account_id: int,
        hashed_password: str,
    ) -> uuid.UUID:
        q = (
            insert(users)
            .values(
                account_id=account_id,
                hashed_password=hashed_password,
            )
            .returning(users.c.id)
        )
        result = await conn.execute(q)
        return result.scalar_one()


    async def get_user_by_id(
        self, conn: AsyncConnection, user_id: uuid.UUID
    ) -> UserInDB | None:
        q = select(users).where(users.c.id == user_id)
        row = await conn.execute(q)
        data = row.mappings().fetchone()
        return UserInDB(**data) if data else None


    async def get_user_by_account_id(
        self, conn: AsyncConnection, account_id: int
    ) -> UserInDB | None:
        q = select(users).where(users.c.account_id == account_id)
        result = await conn.execute(q)
        data = result.mappings().fetchone()
        return UserInDB(**data) if data else None


    async def update_password(
        self,
        conn: AsyncConnection,
        user_id: uuid.UUID,
        new_hashed_password: str,
    ) -> None:
        q = (
            update(users)
            .where(users.c.id == user_id)
            .values(hashed_password=new_hashed_password)
        )
        await conn.execute(q)


    # ------------------------------------------------------------------ #
    #  Refresh Tokens                                                      #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _hash_token(raw_token: str) -> str:
        """SHA-256 от сырого токена. Хранится в БД вместо токена."""
        return hashlib.sha256(raw_token.encode()).hexdigest()


    async def create_refresh_token(
        self,
        conn: AsyncConnection,
        data: RefreshTokenCreate,
    ) -> uuid.UUID:
        q = (
            insert(refresh_tokens)
            .values(
                user_id=data.user_id,
                token_hash=data.token_hash,
                jti=data.jti,
                expires_at=data.expires_at,
                fingerprint=data.fingerprint,
            )
            .returning(refresh_tokens.c.id)
        )
        result = await conn.execute(q)
        return result.scalar_one()


    async def get_refresh_token_by_jti(
        self, conn: AsyncConnection, jti: str
    ) -> dict | None:
        q = select(refresh_tokens).where(refresh_tokens.c.jti == jti)
        row = await conn.execute(q)
        data = row.mappings().fetchone()
        return dict(data) if data else None


    async def get_refresh_token_by_hash(
        self, conn: AsyncConnection, token_hash: str
    ) -> dict | None:
        q = select(refresh_tokens).where(refresh_tokens.c.token_hash == token_hash)
        row = await conn.execute(q)
        data = row.mappings().fetchone()
        return dict(data) if data else None


    async def revoke_token_by_jti(
        self, conn: AsyncConnection, jti: str
    ) -> None:
        q = (
            update(refresh_tokens)
            .where(refresh_tokens.c.jti == jti)
            .values(revoked=True)
        )
        await conn.execute(q)


    async def revoke_all_user_tokens(
        self, conn: AsyncConnection, user_id: uuid.UUID
    ) -> int:
        """Logout со всех устройств. Возвращает кол-во отозванных токенов."""
        q = (
            update(refresh_tokens)
            .where(
                and_(
                    refresh_tokens.c.user_id == user_id,
                    refresh_tokens.c.revoked == False,  # noqa: E712
                )
            )
            .values(revoked=True)
            .returning(refresh_tokens.c.id)
        )
        result = await conn.execute(q)
        return len(result.fetchall())


    async def delete_expired_tokens(self, conn: AsyncConnection) -> int:
        """Вызывается по крону для очистки протухших записей."""
        q = (
            delete(refresh_tokens)
            .where(refresh_tokens.c.expires_at < datetime.now(timezone.utc))
            .returning(refresh_tokens.c.id)
        )
        result = await conn.execute(q)
        return len(result.fetchall())

