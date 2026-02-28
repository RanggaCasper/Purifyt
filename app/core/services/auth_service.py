import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.db.connection import get_db
from app.db.models import TokenBlacklist
from app.db.repositories.user_repository import UserRepository
from app.core.schemas import TokenData

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def _create_token(data: dict, expires_delta: timedelta, token_type: str) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + expires_delta
    to_encode.update({"exp": expire, "iat": now, "jti": str(uuid.uuid4()), "type": token_type})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    delta = expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return _create_token(data, delta, "access")


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    delta = expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return _create_token(data, delta, "refresh")


def create_token_pair(username: str) -> dict:
    payload = {"sub": username}
    return {
        "access_token": create_access_token(payload),
        "refresh_token": create_refresh_token(payload),
        "token_type": "bearer",
    }


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


async def is_token_blacklisted(jti: str, db: AsyncSession) -> bool:
    result = await db.execute(select(TokenBlacklist).where(TokenBlacklist.jti == jti))
    return result.scalar_one_or_none() is not None


async def blacklist_token(token: str, user_id: int, db: AsyncSession) -> None:
    payload = decode_token(token)
    jti = payload.get("jti")
    token_type = payload.get("type", "access")
    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

    exists = await is_token_blacklisted(jti, db)
    if not exists:
        db.add(TokenBlacklist(
            jti=jti,
            user_id=user_id,
            token_type=token_type,
            expires_at=exp,
        ))
        await db.flush()


async def blacklist_all_user_tokens(user_id: int, db: AsyncSession) -> int:
    """Blacklist cannot retroactively find all tokens, but we can mark a
    'block_before' timestamp. Instead, for simplicity, we just rely on
    the caller passing specific tokens to blacklist."""
    pass


async def cleanup_expired_blacklist(db: AsyncSession) -> int:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        delete(TokenBlacklist).where(TokenBlacklist.expires_at < now)
    )
    await db.flush()
    return result.rowcount


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        username: str = payload.get("sub")
        token_type: str = payload.get("type", "access")
        jti: str = payload.get("jti")
        if username is None or token_type != "access":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    if jti and await is_token_blacklisted(jti, db):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    repo = UserRepository(db)
    user = await repo.get_by_username(username)
    if user is None:
        raise credentials_exception
    return user
