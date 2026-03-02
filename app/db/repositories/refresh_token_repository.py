import hashlib
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import RefreshToken


def hash_token(raw_token: str) -> str:
    """Return hex SHA-256 digest of the raw opaque refresh token."""
    return hashlib.sha256(raw_token.encode()).hexdigest()


class RefreshTokenRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # create 
    async def create(
        self,
        user_id: int,
        raw_token: str,
        expires_at: datetime,
        rotated_from_id: Optional[int] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> RefreshToken:
        row = RefreshToken(
            user_id=user_id,
            token_hash=hash_token(raw_token),
            expires_at=expires_at,
            rotated_from_id=rotated_from_id,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        self.db.add(row)
        await self.db.flush()
        await self.db.refresh(row)
        return row

    # lookup 
    async def get_by_token(self, raw_token: str) -> Optional[RefreshToken]:
        """Find an active (non-revoked, non-expired) refresh token row."""
        token_h = hash_token(raw_token)
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_h,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > now,
            )
        )
        return result.scalar_one_or_none()

    # revoke 
    async def revoke(self, token_id: int) -> None:
        """Revoke a single refresh token by id."""
        await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.id == token_id)
            .values(revoked_at=datetime.now(timezone.utc))
        )
        await self.db.flush()

    async def revoke_all_for_user(self, user_id: int) -> int:
        """Revoke every active refresh token for a user (logout-all)."""
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        await self.db.flush()
        return result.rowcount

    async def revoke_by_raw_token(self, raw_token: str) -> bool:
        """Revoke by the raw cookie value. Returns True if found & revoked."""
        row = await self.get_by_token(raw_token)
        if row is None:
            return False
        await self.revoke(row.id)
        return True
