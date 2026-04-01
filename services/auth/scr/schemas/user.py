import re
import uuid
from pydantic import BaseModel, field_validator, Field, ConfigDict


PASSWORD_REGEX = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,72}$"
)


class RegisterRequest(BaseModel):
    account_id: int
    password: str = Field(min_length=8, max_length=72)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not PASSWORD_REGEX.match(v):
            raise ValueError(
                "Password must contain uppercase, lowercase, "
                "digit and special character"
            )
        return v


class LoginRequest(BaseModel):
    account_id: int
    password: str
    # Фингерпринт устройства для Refresh Token Rotation
    fingerprint: str | None = Field(default=None, max_length=255)


class UserOut(BaseModel):
    """Публичное представление пользователя — никаких паролей и хэшей."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: int
    is_active: bool = True
    is_playing: bool = False


class UserInDB(UserOut):
    """
    Внутренняя схема — только для слоя сервисов/репозиториев.
    Никогда не возвращается в API response.
    """
    hashed_password: str