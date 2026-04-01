import uuid
import hashlib
from datetime import datetime, timezone, timedelta

from jose import JWTError, jwt
from fastapi import HTTPException, status

from scr.core.config import settings
from scr.schemas.token import AccessTokenPayload


class TokenService:

    def create_access_token(
        self,
        user_id: uuid.UUID,
    ) -> tuple[str, str, datetime]:
        """
        Возвращает (token, jti, expires_at).
        jti сохраняется в Redis при logout для blacklist.
        """
        jti = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
        payload = {
            "sub": str(user_id),
            "jti": jti,
            "exp": int(expires_at.timestamp()),
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "type": "access",
        }
        token = jwt.encode(
            payload,
            settings.JWT_SECRET_KEY.get_secret_value(),
            algorithm=settings.JWT_ALGORITHM,
        )
        return token, jti, expires_at


    def create_refresh_token(self) -> tuple[str, str, str, datetime]:
        """
        Возвращает (raw_token, token_hash, jti, expires_at).
        raw_token — отдаётся клиенту в httpOnly cookie.
        token_hash — хранится в БД.
        """
        raw_token = str(uuid.uuid4())
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        jti = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        )
        return raw_token, token_hash, jti, expires_at


    def decode_access_token(self, token: str) -> AccessTokenPayload:
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY.get_secret_value(),
                algorithms=[settings.JWT_ALGORITHM],
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        return AccessTokenPayload(**payload)


token_service = TokenService()