from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.logging_config import get_logger
from app.db.models import User

logger = get_logger(__name__)

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, username: str, hashed_password: str) -> User:
        user = User(
            username=username,
            hashed_password=hashed_password,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        logger.info("[USER_REPO] Created user id=%d username='%s'", user.id, user.username)
        return user

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        result = await self.db.execute(select(User).offset(skip).limit(limit))
        return result.scalars().all()

    async def count(self) -> int:
        result = await self.db.execute(select(func.count(User.id)))
        return result.scalar()
