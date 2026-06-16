from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.core.services.auth_service import (
    REFRESH_COOKIE_NAME,
    REFRESH_COOKIE_PATH,
    create_access_token,
    hash_password,
)


# ═══════════════════════════════════════════════════════════════════
# Helpers & Fixtures
# ═══════════════════════════════════════════════════════════════════

def _make_user(
    user_id: int = 1,
    username: str = "testuser",
    password: str = "securePass123",
) -> MagicMock:
    """Create a fake User ORM object."""
    user = MagicMock()
    user.id = user_id
    user.username = username
    user.hashed_password = hash_password(password)
    user.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    user.updated_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    # SQLAlchemy model_validate compat
    user.__class__.__name__ = "User"
    return user


def _make_rt_row(
    rt_id: int = 100,
    user_id: int = 1,
    raw_token: str = "fake-token",
    expires_delta: timedelta = timedelta(days=7),
    revoked: bool = False,
) -> MagicMock:
    """Create a fake RefreshToken ORM row."""
    row = MagicMock()
    row.id = rt_id
    row.user_id = user_id
    row.token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    row.expires_at = datetime.now(timezone.utc) + expires_delta
    row.revoked_at = datetime.now(timezone.utc) if revoked else None
    row.rotated_from_id = None
    row.created_at = datetime.now(timezone.utc)
    return row


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# We patch at the *repository* level so the endpoint code runs through
# the service layer unchanged.

_USER_REPO = "app.api.v1.auth.UserRepository"
_RT_REPO = "app.api.v1.auth.RefreshTokenRepository"


# ═══════════════════════════════════════════════════════════════════
# 1.  POST /auth/login
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.anyio
async def test_login_success_returns_access_token_and_cookie(client: AsyncClient):
    """Login → access_token in JSON body + refresh_token HttpOnly cookie."""
    fake_user = _make_user(password="correct-password")

    with (
        patch(_USER_REPO) as MockUserRepo,
        patch(_RT_REPO) as MockRTRepo,
    ):
        repo_inst = MockUserRepo.return_value
        repo_inst.get_by_username = AsyncMock(return_value=fake_user)

        rt_inst = MockRTRepo.return_value
        rt_inst.create = AsyncMock(return_value=_make_rt_row())

        resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "correct-password"},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] is True
    assert "access_token" in body["data"]
    assert body["data"]["token_type"] == "bearer"
    assert body["data"]["expires_in"] > 0

    # Cookie must be set
    cookie_header = resp.headers.get("set-cookie", "")
    assert REFRESH_COOKIE_NAME in cookie_header
    assert "httponly" in cookie_header.lower()


@pytest.mark.anyio
async def test_login_invalid_credentials_returns_401(client: AsyncClient):
    """Wrong password → 401."""
    fake_user = _make_user(password="correct-password")

    with patch(_USER_REPO) as MockUserRepo:
        repo_inst = MockUserRepo.return_value
        repo_inst.get_by_username = AsyncMock(return_value=fake_user)

        resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "wrong"},
        )

    assert resp.status_code == 401


@pytest.mark.anyio
async def test_login_user_not_found_returns_401(client: AsyncClient):
    """Unknown username → 401."""
    with patch(_USER_REPO) as MockUserRepo:
        repo_inst = MockUserRepo.return_value
        repo_inst.get_by_username = AsyncMock(return_value=None)

        resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "nobody", "password": "anything"},
        )

    assert resp.status_code == 401


@pytest.mark.anyio
async def test_login_no_username_returns_422(client: AsyncClient):
    """Missing username → 422."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"password": "anything"},
    )
    assert resp.status_code == 422


# ═══════════════════════════════════════════════════════════════════
# 2.  GET /auth/me  (protected endpoint)
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.anyio
async def test_me_with_valid_access_token(client: AsyncClient):
    """Valid Bearer token → 200 + user profile."""
    fake_user = _make_user()
    token, _ = create_access_token(user_id=fake_user.id, username=fake_user.username)

    with patch("app.core.services.auth_service.UserRepository") as MockRepo:
        MockRepo.return_value.get_by_id = AsyncMock(return_value=fake_user)

        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["username"] == "testuser"


@pytest.mark.anyio
async def test_me_without_token_returns_401(client: AsyncClient):
    """No Authorization header → 401/403 (HTTPBearer rejects a missing header)."""
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code in (401, 403)


@pytest.mark.anyio
async def test_me_with_expired_access_token_returns_401(client: AsyncClient):
    """Expired access_token → 401."""
    fake_user = _make_user()
    # Create a token that's already expired
    token, _ = create_access_token(
        user_id=fake_user.id,
        username=fake_user.username,
        expires_delta=timedelta(seconds=-1),
    )

    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_me_with_tampered_token_returns_401(client: AsyncClient):
    """Modified JWT signature → 401."""
    token, _ = create_access_token(user_id=1, username="test")
    tampered = token[:-4] + "XXXX"

    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tampered}"},
    )
    assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════
# 3.  POST /auth/refresh  (cookie-based token rotation)
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.anyio
async def test_refresh_success_rotates_tokens(client: AsyncClient):
    """Valid refresh cookie → new access_token + new refresh cookie (rotation)."""
    raw_rt = secrets.token_urlsafe(64)
    fake_user = _make_user()
    fake_rt_row = _make_rt_row(raw_token=raw_rt, user_id=fake_user.id)

    with (
        patch(_USER_REPO) as MockUserRepo,
        patch(_RT_REPO) as MockRTRepo,
    ):
        user_inst = MockUserRepo.return_value
        user_inst.get_by_id = AsyncMock(return_value=fake_user)

        rt_inst = MockRTRepo.return_value
        rt_inst.get_by_token = AsyncMock(return_value=fake_rt_row)
        rt_inst.revoke = AsyncMock()
        rt_inst.create = AsyncMock(return_value=_make_rt_row(rt_id=101))

        resp = await client.post(
            "/api/v1/auth/refresh",
            cookies={REFRESH_COOKIE_NAME: raw_rt},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body["data"]
    assert body["data"]["token_type"] == "bearer"
    assert body["data"]["expires_in"] > 0

    # Old token must have been revoked
    rt_inst.revoke.assert_awaited_once_with(fake_rt_row.id)

    # New refresh cookie must be set
    cookie_header = resp.headers.get("set-cookie", "")
    assert REFRESH_COOKIE_NAME in cookie_header


@pytest.mark.anyio
async def test_refresh_no_cookie_returns_401(client: AsyncClient):
    """No refresh cookie → 401."""
    resp = await client.post("/api/v1/auth/refresh")
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_refresh_invalid_cookie_returns_401(client: AsyncClient):
    """Cookie present but not found in DB (revoked/expired) → 401."""
    with patch(_RT_REPO) as MockRTRepo:
        rt_inst = MockRTRepo.return_value
        rt_inst.get_by_token = AsyncMock(return_value=None)

        resp = await client.post(
            "/api/v1/auth/refresh",
            cookies={REFRESH_COOKIE_NAME: "totally-invalid-token"},
        )

    assert resp.status_code == 401


@pytest.mark.anyio
async def test_refresh_stale_token_after_rotation_returns_401(client: AsyncClient):
    """After rotation, using the OLD refresh token must fail (already revoked)."""
    old_rt = secrets.token_urlsafe(64)

    with patch(_RT_REPO) as MockRTRepo:
        rt_inst = MockRTRepo.return_value
        # Old token is revoked → get_by_token returns None
        rt_inst.get_by_token = AsyncMock(return_value=None)

        resp = await client.post(
            "/api/v1/auth/refresh",
            cookies={REFRESH_COOKIE_NAME: old_rt},
        )

    assert resp.status_code == 401


@pytest.mark.anyio
async def test_refresh_user_deleted_returns_401(client: AsyncClient):
    """Refresh token valid in DB but user no longer exists → 401."""
    raw_rt = secrets.token_urlsafe(64)
    fake_rt_row = _make_rt_row(raw_token=raw_rt, user_id=999)

    with (
        patch(_USER_REPO) as MockUserRepo,
        patch(_RT_REPO) as MockRTRepo,
    ):
        user_inst = MockUserRepo.return_value
        user_inst.get_by_id = AsyncMock(return_value=None)

        rt_inst = MockRTRepo.return_value
        rt_inst.get_by_token = AsyncMock(return_value=fake_rt_row)

        resp = await client.post(
            "/api/v1/auth/refresh",
            cookies={REFRESH_COOKIE_NAME: raw_rt},
        )

    assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════
# 4.  POST /auth/logout
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.anyio
async def test_logout_revokes_token_and_clears_cookie(client: AsyncClient):
    """Logout with valid cookie → token revoked in DB + cookie expired."""
    raw_rt = secrets.token_urlsafe(64)

    with patch(_RT_REPO) as MockRTRepo:
        rt_inst = MockRTRepo.return_value
        rt_inst.revoke_by_raw_token = AsyncMock(return_value=True)

        resp = await client.post(
            "/api/v1/auth/logout",
            cookies={REFRESH_COOKIE_NAME: raw_rt},
        )

    assert resp.status_code == 204
    rt_inst.revoke_by_raw_token.assert_awaited_once_with(raw_rt)

    # Cookie must be deleted (Max-Age=0 or expires in the past)
    cookie_header = resp.headers.get("set-cookie", "")
    assert REFRESH_COOKIE_NAME in cookie_header
    # FastAPI/Starlette deletes cookies by setting Max-Age=0
    assert "max-age=0" in cookie_header.lower() or '=""' in cookie_header


@pytest.mark.anyio
async def test_logout_without_cookie_returns_204(client: AsyncClient):
    """Logout without a cookie → still 204 (idempotent)."""
    resp = await client.post("/api/v1/auth/logout")
    assert resp.status_code == 204


# ═══════════════════════════════════════════════════════════════════
# 5.  POST /auth/register
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.anyio
async def test_register_success(client: AsyncClient):
    """Valid registration → 201 + user data."""
    fake_user = _make_user()

    with patch(_USER_REPO) as MockUserRepo:
        repo_inst = MockUserRepo.return_value
        repo_inst.get_by_username = AsyncMock(return_value=None)
        repo_inst.create = AsyncMock(return_value=fake_user)

        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "password": "securePass123",
            },
        )

    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] is True
    assert body["data"]["username"] == "testuser"


@pytest.mark.anyio
async def test_register_duplicate_username(client: AsyncClient):
    """Duplicate username → 400."""
    fake_user = _make_user()

    with patch(_USER_REPO) as MockUserRepo:
        repo_inst = MockUserRepo.return_value
        repo_inst.get_by_username = AsyncMock(return_value=fake_user)

        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "password": "securePass123",
            },
        )

    assert resp.status_code == 400


@pytest.mark.anyio
# ═══════════════════════════════════════════════════════════════════
# 6.  Full flow: Register → Login → Me → Refresh → Logout → Stale
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.anyio
async def test_full_auth_lifecycle(client: AsyncClient):
    """
    End-to-end scenario (mocked DB):
      register → login → /me → refresh (rotate) → /me → logout → stale refresh
    """
    fake_user = _make_user(password="lifecycle-pw")
    raw_rt_1 = "first-refresh-token-value"
    raw_rt_2 = "second-refresh-token-value"
    rt_row_1 = _make_rt_row(rt_id=10, raw_token=raw_rt_1, user_id=fake_user.id)
    rt_row_2 = _make_rt_row(rt_id=11, raw_token=raw_rt_2, user_id=fake_user.id)

    # We control generate_refresh_token to return predictable values
    gen_rt_calls = iter([raw_rt_1, raw_rt_2])

    with (
        patch(_USER_REPO) as MockUserRepo,
        patch(_RT_REPO) as MockRTRepo,
        patch(
            "app.api.v1.auth.generate_refresh_token",
            side_effect=lambda: next(gen_rt_calls),
        ),
        patch(
            "app.core.services.auth_service.UserRepository"
        ) as MockAuthUserRepo,
    ):
        user_inst = MockUserRepo.return_value
        auth_user_inst = MockAuthUserRepo.return_value

        # Register
        user_inst.get_by_username = AsyncMock(return_value=None)
        user_inst.create = AsyncMock(return_value=fake_user)

        resp = await client.post(
            "/api/v1/auth/register",
            json={"username": "testuser", "password": "lifecycle-pw"},
        )
        assert resp.status_code == 201

        # Login
        user_inst.get_by_username = AsyncMock(return_value=fake_user)
        rt_inst = MockRTRepo.return_value
        rt_inst.create = AsyncMock(return_value=rt_row_1)

        resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "lifecycle-pw"},
        )
        assert resp.status_code == 200
        access_token_1 = resp.json()["data"]["access_token"]
        assert access_token_1

        # /me with access_token_1
        auth_user_inst.get_by_id = AsyncMock(return_value=fake_user)
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token_1}"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["username"] == "testuser"

        # Refresh – rotate from rt_row_1 → rt_row_2
        user_inst.get_by_id = AsyncMock(return_value=fake_user)
        rt_inst.get_by_token = AsyncMock(return_value=rt_row_1)
        rt_inst.revoke = AsyncMock()
        rt_inst.create = AsyncMock(return_value=rt_row_2)

        resp = await client.post(
            "/api/v1/auth/refresh",
            cookies={REFRESH_COOKIE_NAME: raw_rt_1},
        )
        assert resp.status_code == 200
        access_token_2 = resp.json()["data"]["access_token"]
        assert access_token_2
        rt_inst.revoke.assert_awaited_once_with(rt_row_1.id)

        # /me with new access_token_2
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token_2}"},
        )
        assert resp.status_code == 200

        # Logout
        rt_inst.revoke_by_raw_token = AsyncMock(return_value=True)
        resp = await client.post(
            "/api/v1/auth/logout",
            cookies={REFRESH_COOKIE_NAME: raw_rt_2},
        )
        assert resp.status_code == 204

        # Stale refresh with old token (rt_row_1 already revoked) → 401
        rt_inst.get_by_token = AsyncMock(return_value=None)
        resp = await client.post(
            "/api/v1/auth/refresh",
            cookies={REFRESH_COOKIE_NAME: raw_rt_1},
        )
        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════
# 7.  Unit tests for token hash in repository
# ═══════════════════════════════════════════════════════════════════

class TestRefreshTokenHash:
    def test_hash_is_sha256_hex(self):
        from app.db.repositories.refresh_token_repository import hash_token
        raw = "some-opaque-token"
        h = hash_token(raw)
        assert len(h) == 64  # SHA-256 hex = 64 chars
        assert h == hashlib.sha256(raw.encode()).hexdigest()

    def test_different_tokens_produce_different_hashes(self):
        from app.db.repositories.refresh_token_repository import hash_token
        assert hash_token("token-a") != hash_token("token-b")

    def test_same_token_produces_same_hash(self):
        from app.db.repositories.refresh_token_repository import hash_token
        assert hash_token("abc") == hash_token("abc")
