from fastapi import APIRouter, Depends, Response, status, Request
from sqlalchemy.ext.asyncio import AsyncConnection
from redis.asyncio import Redis

from scr.core.database import get_conn
from scr.core.redis import get_redis
from scr.core.config import settings
from scr.dependencies.auth import (
    get_current_user_optional,
    get_refresh_token,
    get_optional_refresh_token,
)
from scr.dependencies.services import get_auth_service
from scr.schemas.user import RegisterRequest, LoginRequest, UserOut
from scr.schemas.token import TokenResponse, AccessTokenPayload
from scr.schemas.common import MessageResponse
from scr.services.auth_service import AuthService

from fastapi import HTTPException


router = APIRouter(prefix="/auth", tags=["auth"])

def _set_refresh_cookie(response: Response, raw_token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=raw_token,
        httponly=True,        # недоступен из JS
        secure=settings.COOKIE_SECURE,
        samesite="lax",       # CSRF защита
        max_age=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/api/v1/auth",  # cookie отправляется только на auth эндпоинты
    )


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    data: RegisterRequest,
    conn: AsyncConnection = Depends(get_conn),
    service: AuthService = Depends(get_auth_service),
):
    return await service.register(conn, data)


@router.post("/login", response_model=TokenResponse)
async def login(
    response: Response,
    data: LoginRequest,
    conn: AsyncConnection = Depends(get_conn),
    redis: Redis = Depends(get_redis),
    service: AuthService = Depends(get_auth_service),
):
    token_response, raw_refresh = await service.login(
        conn, redis, data, fingerprint=data.fingerprint
    )
    _set_refresh_cookie(response, raw_refresh)
    return token_response


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    response: Response,
    refresh_token: str = Depends(get_refresh_token),
    fingerprint: str | None = None,
    conn: AsyncConnection = Depends(get_conn),
    service: AuthService = Depends(get_auth_service),
):
    token_response, raw_refresh = await service.refresh(
        conn,
        refresh_token,
        fingerprint=fingerprint,
    )
    _set_refresh_cookie(response, raw_refresh)
    return token_response


@router.post("/logout", response_model=MessageResponse)
async def logout(
    response: Response,
    payload: AccessTokenPayload | None = Depends(get_current_user_optional),
    refresh_token: str | None = Depends(get_optional_refresh_token),
    conn: AsyncConnection = Depends(get_conn),
    redis: Redis = Depends(get_redis),
    service: AuthService = Depends(get_auth_service),
):
    if payload is None and refresh_token is None:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    await service.logout(
        conn,
        redis,
        payload.jti if payload else None,
        payload.exp if payload else None,
        refresh_token,
    )
    # Удаляем cookie на клиенте
    response.delete_cookie("refresh_token", path="/api/v1/auth")
    return MessageResponse(message="Logged out successfully")


@router.get("/debug/cookies")
async def debug_cookies(request: Request):
    cookies = request.cookies
    print("COOKIES:", cookies)
    return {
        "cookies": cookies,
    }

