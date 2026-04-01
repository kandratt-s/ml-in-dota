import uuid
from datetime import datetime
from pydantic import BaseModel


class TokenResponse(BaseModel):
    """Ответ на /login и /refresh."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # секунды до истечения access_token
    # refresh_token передаётся через httpOnly cookie, не в теле —
    # поэтому его здесь нет


class AccessTokenPayload(BaseModel):
    """
    Содержимое JWT payload после декодирования.
    sub — subject (user_id), jti — уникальный ID токена для blacklist.
    """
    sub: str             # user_id как строка
    jti: str             # uuid4, уникален для каждого токена
    exp: int             # Unix timestamp истечения
    iat: int             # Unix timestamp выдачи
    type: str = "access" # "access" | "refresh"


class RefreshTokenCreate(BaseModel):
    """Данные для записи refresh_token в БД."""
    user_id: uuid.UUID
    token_hash: str   # SHA-256 от сырого токена
    jti: str
    expires_at: datetime
    fingerprint: str | None = None
