from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.connection import get_db
from app.db.repositories.user_repository import UserRepository
from app.core.schemas import Token, UserCreate, UserResponse
from app.core.services.auth_service import (
    hash_password,
    verify_password,
    create_token_pair,
    decode_token,
    blacklist_token,
    is_token_blacklisted,
    get_current_user,
    oauth2_scheme,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)

    if await repo.get_by_username(payload.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    if await repo.get_by_email(payload.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    user = await repo.create(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    repo = UserRepository(db)
    user = await repo.get_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    tokens = create_token_pair(user.username)
    return tokens


@router.post("/refresh", response_model=Token)
async def refresh_token(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """Exchange a valid refresh_token for a new access_token + refresh_token pair.
    The old refresh_token is blacklisted to prevent reuse."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(body.refresh_token)
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        jti: str = payload.get("jti")
        if username is None or token_type != "refresh":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    if jti and await is_token_blacklisted(jti, db):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked",
        )

    repo = UserRepository(db)
    user = await repo.get_by_username(username)
    if user is None:
        raise credentials_exception

    await blacklist_token(body.refresh_token, user.id, db)
    await db.commit()

    tokens = create_token_pair(user.username)
    return tokens


@router.post("/logout")
async def logout(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """Revoke the current access_token. Optionally pass refresh_token in body to revoke it too."""
    try:
        payload = decode_token(token)
        username = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    repo = UserRepository(db)
    user = await repo.get_by_username(username)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    await blacklist_token(token, user.id, db)
    await db.commit()
    return {"message": "Successfully logged out"}


class LogoutAllRequest(BaseModel):
    refresh_token: str | None = None


@router.post("/logout/all")
async def logout_all(
    body: LogoutAllRequest = LogoutAllRequest(),
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """Revoke current access_token and optionally a refresh_token."""
    try:
        payload = decode_token(token)
        username = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    repo = UserRepository(db)
    user = await repo.get_by_username(username)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    await blacklist_token(token, user.id, db)

    if body.refresh_token:
        try:
            await blacklist_token(body.refresh_token, user.id, db)
        except JWTError:
            pass

    await db.commit()
    return {"message": "All provided tokens have been revoked"}


@router.get("/me", response_model=UserResponse)
async def me(current_user=Depends(get_current_user)):
    return current_user
