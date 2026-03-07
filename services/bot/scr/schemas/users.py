from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class UserCreate(BaseModel):
    """Schema for creating a user"""
    telegram_id: int = Field(..., gt=0, description="Telegram user ID")
    token: str = Field(..., min_length=1, description="User token")


class UserUpdate(BaseModel):
    """Schema for updating a user"""
    token: str = Field(..., min_length=1, description="User token")


class UserResponse(BaseModel):
    """Schema for user response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="User database ID")
    telegram_id: int = Field(..., description="Telegram user ID")
    token: str = Field(..., description="User token")
    created_at: datetime = Field(..., description="User creation timestamp")


class UserInDB(UserResponse):
    """Schema for user in database (same as response for now)"""
    pass