from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import OAuth2PasswordBearer
from redis.asyncio import Redis

from scr.core.redis import get_redis
from scr.schemas.token import AccessTokenPayload
from scr.services.token_service import token_service

# tokenUrl указывает Swagger UI, куда слать credentials для кнопки Authorize
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    redis: Redis = Depends(get_redis),
) -> AccessTokenPayload:
    """
    Основная зависимость для защищённых роутов.
    Проверяет подпись JWT и blacklist в Redis.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = token_service.decode_access_token(token)

    # Проверяем blacklist — попадает ли jti в отозванные
    if await redis.exists(f"blacklist:{payload.jti}"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )

    return payload


async def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme),
    redis: Redis = Depends(get_redis),
) -> AccessTokenPayload | None:
    """Опциональная версия: None, если access token не передан."""
    if not token:
        return None

    payload = token_service.decode_access_token(token)
    if await redis.exists(f"blacklist:{payload.jti}"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )
    return payload


async def get_current_active_user(
    payload: AccessTokenPayload = Depends(get_current_user),
) -> AccessTokenPayload:
    """Можно расширить: проверять is_active прямо здесь через БД."""
    return payload


def get_refresh_token(
    refresh_token: str | None = Cookie(default=None, alias="refresh_token"),
) -> str:
    """
    Читает сырой refresh_token из httpOnly cookie.
    """
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )
    return refresh_token


def get_optional_refresh_token(
    refresh_token: str | None = Cookie(default=None, alias="refresh_token"),
) -> str | None:
    """Опциональный refresh_token для logout-сценария."""
    return refresh_token
