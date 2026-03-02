import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.logging_config import get_logger
from app.config.settings import get_settings
from app.db.connection import get_db
from app.db.repositories.user_repository import UserRepository

logger = get_logger(__name__)
settings = get_settings()

# password hashing 
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# JWT (access token only) 
oauth2_scheme = HTTPBearer()

# Cookie path must match the endpoint prefix so the browser sends the cookie
# only to /api/v1/auth/* routes.
REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_PATH = "/api/v1/auth"

def create_access_token(
    user_id: int,
    username: str,
    expires_delta: Optional[timedelta] = None,
) -> tuple[str, int]:
    """Return (encoded_jwt, expires_in_seconds)."""
    delta = expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    now = datetime.now(timezone.utc)
    expire = now + delta
    payload = {
        "sub": str(user_id),
        "username": username,
        "type": "access",
        "iat": now,
        "exp": expire,
        "jti": str(uuid.uuid4()),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    logger.debug("[AUTH] Access token created for user_id=%d, expires_in=%ds", user_id, int(delta.total_seconds()))
    return token, int(delta.total_seconds())

def decode_access_token(token: str) -> dict:
    """Decode & validate an access JWT.  Raises JWTError on failure."""
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    if payload.get("type") != "access":
        raise JWTError("Not an access token")
    return payload

# Opaque refresh token 
def generate_refresh_token() -> str:
    """Generate a cryptographically secure random token (64 bytes, URL-safe)."""
    return secrets.token_urlsafe(64)

# Cookie helpers 
def set_refresh_cookie(response: Response, raw_token: str) -> None:
    """Set the HttpOnly refresh-token cookie on *response*."""
    max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=raw_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        path=REFRESH_COOKIE_PATH,
        max_age=max_age,
        domain=settings.COOKIE_DOMAIN,
    )

def delete_refresh_cookie(response: Response) -> None:
    """Expire / delete the refresh-token cookie."""
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        path=REFRESH_COOKIE_PATH,
        domain=settings.COOKIE_DOMAIN,
    )

# FastAPI dependency: get current user from Bearer token 
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """Validate the access JWT in the Authorization header and return the User object."""
    token = credentials.credentials
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise credentials_exc
        user_id = int(user_id_str)
    except (JWTError, ValueError):
        logger.warning("[AUTH] Invalid access token presented")
        raise credentials_exc

    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if user is None:
        logger.warning("[AUTH] Token valid but user_id=%d not found in DB", user_id)
        raise credentials_exc
    logger.debug("[AUTH] Authenticated user_id=%d username=%s", user.id, user.username)
    return user