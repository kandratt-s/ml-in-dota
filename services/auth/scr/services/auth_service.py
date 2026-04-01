import uuid
import hashlib
from datetime import timezone

from fastapi import HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncConnection

from scr.repositories.auth_repo import AuthRepository
from scr.schemas.user import RegisterRequest, LoginRequest, UserOut
from scr.schemas.token import TokenResponse, RefreshTokenCreate
from .password_service import hash_password, verify_password, needs_rehash
from .token_service import token_service


class AuthService:

    def __init__(self, repo: AuthRepository):
        self.repo = repo

    # ------------------------------------------------------------------ #
    #  Register                                                            #
    # ------------------------------------------------------------------ #

    async def register(
        self,
        conn: AsyncConnection,
        data: RegisterRequest,
    ) -> UserOut:
        hashed = hash_password(data.password)
        user_id = await self.repo.create_user(
            conn,
            account_id=data.account_id,
            hashed_password=hashed,
        )
        user = await self.repo.get_user_by_id(conn, user_id)
        return UserOut.model_validate(user)

    # ------------------------------------------------------------------ #
    #  Login                                                               #
    # ------------------------------------------------------------------ #

    async def login(
        self,
        conn: AsyncConnection,
        redis: Redis,
        data: LoginRequest,
        fingerprint: str | None = None,
    ) -> tuple[TokenResponse, str]:
        """
        Возвращает (TokenResponse, raw_refresh_token).
        raw_refresh_token роутер кладёт в httpOnly cookie.
        """
        user = await self.repo.get_user_by_account_id(conn, data.account_id)

        # Важно: одна и та же ошибка для "нет такого email" и "неверный пароль"
        # — не даём атакующему перечислять зарегистрированные email
        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        if not getattr(user, "is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled",
            )

        # Если алгоритм хэширования обновился — пересохраняем хэш
        if needs_rehash(user.hashed_password):
            new_hash = hash_password(data.password)
            await self.repo.update_password(conn, user.id, new_hash)

        # Выдаём токены
        access_token, _, _ = token_service.create_access_token(user.id)
        raw_refresh, token_hash, jti, expires_at = token_service.create_refresh_token()

        await self.repo.create_refresh_token(
            conn,
            RefreshTokenCreate(
                user_id=user.id,
                token_hash=token_hash,
                jti=jti,
                expires_at=expires_at,
                fingerprint=fingerprint,
            ),
        )

        token_response = TokenResponse(
            access_token=access_token,
            expires_in=60 * 15,  # 15 минут в секундах
        )
        return token_response, raw_refresh

    # ------------------------------------------------------------------ #
    #  Refresh                                                             #
    # ------------------------------------------------------------------ #

    async def refresh(
        self,
        conn: AsyncConnection,
        raw_refresh_token: str,
        fingerprint: str | None = None,
    ) -> tuple[TokenResponse, str]:
        """
        Refresh Token Rotation:
        1. Находим запись по jti
        2. Проверяем валидность и fingerprint
        3. Отзываем старый токен
        4. Выдаём новую пару
        """
        token_hash = hashlib.sha256(raw_refresh_token.encode()).hexdigest()
        token_record = await self.repo.get_refresh_token_by_hash(conn, token_hash)

        if not token_record:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token not found")

        if token_record["revoked"]:
            # Если уже отозван — кто-то повторно использует старый токен.
            # Это признак кражи: отзываем ВСЕ токены пользователя.
            await self.repo.revoke_all_user_tokens(conn, token_record["user_id"])
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token reuse detected. All sessions terminated.",
            )

        if token_record["expires_at"].replace(tzinfo=timezone.utc) < \
                __import__("datetime").datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")

        # Проверяем фингерпринт — защита от кражи куки с другого устройства
        if (
            token_record["fingerprint"]
            and fingerprint is not None
            and fingerprint != token_record["fingerprint"]
        ):
            await self.repo.revoke_all_user_tokens(conn, token_record["user_id"])
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Device mismatch. All sessions terminated.",
            )

        # Rotation: отзываем старый, выдаём новый
        await self.repo.revoke_token_by_jti(conn, token_record["jti"])

        user = await self.repo.get_user_by_id(conn, token_record["user_id"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        access_token, _, _ = token_service.create_access_token(user.id)
        raw_refresh, token_hash, new_jti, expires_at = token_service.create_refresh_token()
        next_fingerprint = fingerprint if fingerprint is not None else token_record["fingerprint"]

        await self.repo.create_refresh_token(
            conn,
            RefreshTokenCreate(
                user_id=user.id,
                token_hash=token_hash,
                jti=new_jti,
                expires_at=expires_at,
                fingerprint=next_fingerprint,
            ),
        )

        return TokenResponse(access_token=access_token, expires_in=900), raw_refresh

    # ------------------------------------------------------------------ #
    #  Logout                                                              #
    # ------------------------------------------------------------------ #

    async def logout(
        self,
        conn: AsyncConnection,
        redis: Redis,
        access_jti: str | None = None,
        access_exp: int | None = None,
        refresh_token: str | None = None,
    ) -> None:
        """
        Двойная инвалидация:
        - access_token кладём в Redis blacklist до его истечения
        - refresh_token отзываем в БД
        """
        import time

        if access_jti and access_exp is not None:
            ttl = max(0, int(access_exp - time.time()))
            if ttl > 0:
                await redis.setex(f"blacklist:{access_jti}", ttl, "1")

        if refresh_token:
            token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
            token_record = await self.repo.get_refresh_token_by_hash(conn, token_hash)
            if token_record:
                await self.repo.revoke_token_by_jti(conn, token_record["jti"])

    async def logout_all(
        self,
        conn: AsyncConnection,
        redis: Redis,
        user_id: uuid.UUID,
        access_jti: str,
        access_exp: int,
    ) -> None:
        """Logout со всех устройств."""
        import time

        ttl = max(0, int(access_exp - time.time()))
        if ttl > 0:
            await redis.setex(f"blacklist:{access_jti}", ttl, "1")

        await self.repo.revoke_all_user_tokens(conn, user_id)

