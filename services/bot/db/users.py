from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from scr.models.database import User
from scr.schemas.users import UserCreate, UserUpdate, UserResponse


class UserRepository:
    """Repository for user-related database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """Create a new user and return user data."""
        try:
            db_user = User(
                telegram_id=user_data.telegram_id, 
                token=user_data.token
            )
            self.session.add(db_user)
            await self.session.commit()
            await self.session.refresh(db_user)
            return UserResponse.model_validate(db_user)
        except IntegrityError:
            await self.session.rollback()
            raise ValueError(f"User with telegram_id {user_data.telegram_id} already exists")

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[UserResponse]:
        """Retrieve a user by their Telegram ID."""
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        return UserResponse.model_validate(user) if user else None

    async def update_user_token(self, telegram_id: int, token: str) -> Optional[UserResponse]:
        """Update user token by telegram_id."""
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            return None
            
        user.token = token
        await self.session.commit()
        await self.session.refresh(user)
        return UserResponse.model_validate(user)

    async def user_exists(self, telegram_id: int) -> bool:
        """Check if user exists by telegram_id."""
        stmt = select(User.id).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None