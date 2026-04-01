from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Единый формат ошибок во всём сервисе."""
    detail: str
    code: str | None = None  # машиночитаемый код: "invalid_credentials", "user_not_found"


class MessageResponse(BaseModel):
    """Для ответов без данных: logout, verify email и т.д."""
    message: str