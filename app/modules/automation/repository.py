from typing import Optional, List
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import get_logger
from app.db.models import CookieAccount

logger = get_logger(__name__)


class CookieAccountRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upsert(
        self,
        email: str,
        cookie_path: str,
        cookie_count: int = 0,
        channel_name: Optional[str] = None,
    ) -> CookieAccount:
        """Create or update cookie account by email."""
        existing = await self.get_by_email(email)
        if existing:
            existing.cookie_path = cookie_path
            existing.cookie_count = cookie_count
            existing.is_active = 1
            if channel_name:
                existing.channel_name = channel_name
            await self.db.flush()
            await self.db.refresh(existing)
            logger.info("[COOKIE_REPO] Updated cookie account email=%s cookies=%d", email, cookie_count)
            return existing

        account = CookieAccount(
            email=email,
            cookie_path=cookie_path,
            cookie_count=cookie_count,
            channel_name=channel_name,
            is_active=1,
        )
        self.db.add(account)
        await self.db.flush()
        await self.db.refresh(account)
        logger.info("[COOKIE_REPO] Created cookie account email=%s cookies=%d", email, cookie_count)
        return account

    async def get_by_email(self, email: str) -> Optional[CookieAccount]:
        result = await self.db.execute(
            select(CookieAccount).where(CookieAccount.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, account_id: int) -> Optional[CookieAccount]:
        result = await self.db.execute(
            select(CookieAccount).where(CookieAccount.id == account_id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, active_only: bool = False) -> List[CookieAccount]:
        stmt = select(CookieAccount).order_by(CookieAccount.updated_at.desc())
        if active_only:
            stmt = stmt.where(CookieAccount.is_active == 1)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def delete_by_email(self, email: str) -> bool:
        result = await self.db.execute(
            delete(CookieAccount).where(CookieAccount.email == email)
        )
        await self.db.flush()
        deleted = result.rowcount > 0
        logger.info("[COOKIE_REPO] delete_by_email email=%s deleted=%s", email, deleted)
        return deleted

    async def deactivate(self, email: str) -> bool:
        result = await self.db.execute(
            update(CookieAccount)
            .where(CookieAccount.email == email)
            .values(is_active=0)
        )
        await self.db.flush()
        return result.rowcount > 0
