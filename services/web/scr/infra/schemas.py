from pydantic import BaseModel, Field
from datetime import datetime


class RegisterRequest(BaseModel):
    account_id: int
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    account_id: int
    password: str
    fingerprint: str | None = None


class AuthResponse(BaseModel):
    ok: bool
    message: str | None = None


class HeatmapResponse(BaseModel):
    version: int
    grid_size: int
    heat: list[list[float]]
    max_value: float
    updated_at: datetime
    session_active: bool