from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.logging_config import get_logger
from app.config.settings import get_settings
from app.db.connection import get_db
from app.db.repositories.user_repository import UserRepository
from app.db.repositories.refresh_token_repository import RefreshTokenRepository
from app.core.schemas import LoginRequest, Token, UserCreate, UserResponse
from app.utils.response_formatter import APIResponse, success_response
from app.core.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    generate_refresh_token,
    set_refresh_cookie,
    delete_refresh_cookie,
    get_current_user,
    REFRESH_COOKIE_NAME,
)

logger = get_logger(__name__)
settings = get_settings()
router = APIRouter(prefix="/auth", tags=["Authentication"])


# helpers 
async def _issue_tokens(
    user_id: int,
    username: str,
    response: Response,
    db: AsyncSession,
    rotated_from_id: int | None = None,
    request: Request | None = None,
) -> dict:
    """Create an access JWT + opaque refresh token, persist refresh in DB,
    set refresh cookie, and return the JSON-safe token dict."""
    # Access token
    access_token, expires_in = create_access_token(user_id, username)

    # Refresh token (opaque)
    raw_refresh = generate_refresh_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    rt_repo = RefreshTokenRepository(db)
    await rt_repo.create(
        user_id=user_id,
        raw_token=raw_refresh,
        expires_at=expires_at,
        rotated_from_id=rotated_from_id,
        user_agent=request.headers.get("user-agent") if request else None,
        ip_address=request.client.host if request and request.client else None,
    )

    # Set HttpOnly cookie
    set_refresh_cookie(response, raw_refresh)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": expires_in,
    }


# POST /auth/register 
@router.post("/register", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
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
    logger.info("[AUTH] User registered — id=%d username=%s", user.id, user.username)
    return success_response(
        data=UserResponse.model_validate(user),
        message="User registered successfully",
    )


# POST /auth/login 
@router.post("/login", response_model=APIResponse)
async def login(
    request: Request,
    response: Response,
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate with email/username + password.
    Returns access_token in JSON, sets refresh_token as HttpOnly cookie.
    """
    repo = UserRepository(db)

    # Resolve user by email or username
    user = None
    if payload.email:
        user = await repo.get_by_email(payload.email)
    elif payload.username:
        user = await repo.get_by_username(payload.username)
    else:
        raise HTTPException(status_code=400, detail="Provide email or username")

    if not user or not verify_password(payload.password, user.hashed_password):
        logger.warning("[AUTH] Login failed — incorrect credentials for email=%s username=%s", payload.email, payload.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    tokens = await _issue_tokens(
        user_id=user.id,
        username=user.username,
        response=response,
        db=db,
        request=request,
    )
    logger.info("[AUTH] Login successful — user_id=%d username=%s", user.id, user.username)
    return success_response(data=tokens, message="Login successful")


# POST /auth/login (form-data, for Swagger UI compat) 
@router.post("/login/form", response_model=APIResponse, include_in_schema=False)
async def login_form(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """OAuth2-compatible form login (used by Swagger 'Authorize' button)."""
    repo = UserRepository(db)
    user = await repo.get_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    tokens = await _issue_tokens(
        user_id=user.id,
        username=user.username,
        response=response,
        db=db,
        request=request,
    )
    return success_response(data=tokens, message="Login successful")


# POST /auth/refresh 
@router.post("/refresh", response_model=APIResponse)
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Exchange a valid refresh_token cookie for a new access_token + rotated
    refresh_token.  The old refresh token is revoked (rotation).
    """
    raw_token: str | None = request.cookies.get(REFRESH_COOKIE_NAME)

    if not raw_token:
        delete_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    rt_repo = RefreshTokenRepository(db)
    token_row = await rt_repo.get_by_token(raw_token)

    if token_row is None:
        # Token invalid / expired / already revoked → clean cookie
        delete_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Look up user
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(token_row.user_id)
    if user is None:
        delete_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # rotation: revoke old, issue new 
    await rt_repo.revoke(token_row.id)
    logger.info("[AUTH] Token refreshed — user_id=%d old_token_id=%d", user.id, token_row.id)

    tokens = await _issue_tokens(
        user_id=user.id,
        username=user.username,
        response=response,
        db=db,
        rotated_from_id=token_row.id,
        request=request,
    )
    return success_response(data=tokens, message="Token refreshed successfully")


# POST /auth/logout 
@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Revoke the refresh token stored in the cookie and clear the cookie.
    Does NOT require an access_token – a user can always log out.
    """
    raw_token: str | None = request.cookies.get(REFRESH_COOKIE_NAME)

    if raw_token:
        rt_repo = RefreshTokenRepository(db)
        await rt_repo.revoke_by_raw_token(raw_token)

    delete_refresh_cookie(response)
    logger.info("[AUTH] User logged out")
    return None  # 204 No Content


# GET /auth/me 
@router.get("/me", response_model=APIResponse)
async def me(current_user=Depends(get_current_user)):
    """Return the profile of the currently authenticated user."""
    return success_response(data=UserResponse.model_validate(current_user))
