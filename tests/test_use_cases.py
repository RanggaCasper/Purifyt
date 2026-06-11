"""
Use-Case based test suite for Purifyt.

Each test class maps to a Use Case in docs/use_case_specification.md:

  UC-01 Login                          -> see tests/test_auth_flow.py
  UC-02 Register                       -> see tests/test_auth_flow.py
  UC-03 Manage Profile                 -> TestUC03ManageProfile
  UC-04 Manage Dataset                 -> TestUC04ManageDataset
  UC-05 Predict Comments               -> TestUC05PredictComments
  UC-06 Manage Cookie YouTube Accounts -> TestUC06ManageCookieAccounts
  UC-07 Delete Gambling Comments       -> TestUC07DeleteGamblingComments
  UC-08 Explore Video                  -> TestUC08ExploreVideo
  UC-09 Explore Channel                -> TestUC09ExploreChannel

Strategy
--------
Protected endpoints depend on `get_current_user` (Bearer JWT) and `get_db`
(an AsyncSession).  Instead of standing up a real database, we override both
FastAPI dependencies with lightweight fakes and patch the repository/service
classes the endpoint instantiates.  This keeps tests fast and DB-free while
still exercising the real endpoint code paths.
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.db.connection import get_db
from app.core.services.auth_service import get_current_user


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def anyio_backend():
    return "asyncio"


def _fake_user(user_id: int = 1, username: str = "tester", email: str = "tester@example.com"):
    return SimpleNamespace(
        id=user_id,
        username=username,
        email=email,
        created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )


class _FakeSession:
    """Minimal async DB session stand-in for endpoints that only pass `db`
    through to repositories (which we patch) plus an occasional commit/execute."""

    def __init__(self):
        self.execute = AsyncMock()
        self.commit = AsyncMock()
        self.flush = AsyncMock()
        self.rollback = AsyncMock()
        self.close = AsyncMock()


@pytest.fixture
def fake_db():
    return _FakeSession()


@pytest.fixture
def current_user():
    return _fake_user()


@pytest.fixture
async def client(fake_db, current_user):
    """Authenticated client: get_db + get_current_user are overridden so any
    endpoint behind the auth dependency is reachable."""

    async def _override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = lambda: current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def anon_client():
    """Unauthenticated client (no dependency overrides) for testing 401s."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _comment_obj(cid: int = 1, dataset_id: int = 1, label: str | None = None):
    return SimpleNamespace(
        id=cid,
        dataset_id=dataset_id,
        video_id="vid123",
        title="Some Video",
        channel_name="Some Channel",
        date=None,
        author="author",
        comment="ini komentar",
        label=label,
        clean_comment="ini komentar",
        predicted_label="0",
        source=SimpleNamespace(value="youtube_api"),
        source_detail="youtube:vid123",
        created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )


def _dataset_obj(ds_id: int = 1):
    return SimpleNamespace(
        id=ds_id,
        name="My Dataset",
        description="desc",
        source=SimpleNamespace(value="youtube_api"),
        source_url="https://youtube.com/watch?v=vid123",
        owner_id=1,
        created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )


# ═══════════════════════════════════════════════════════════════════
# UC-03  Manage Profile  (users list/detail)
#   /auth/me, /auth/refresh, /auth/logout already covered in test_auth_flow.py
# ═══════════════════════════════════════════════════════════════════

class TestUC03ManageProfile:
    """UC-03: list & view users (profile management)."""

    @pytest.mark.anyio
    async def test_list_users_success(self, client: AsyncClient):
        """Main flow: authenticated user lists users with pagination."""
        with patch("app.api.v1.users.UserRepository") as MockRepo:
            inst = MockRepo.return_value
            inst.get_all = AsyncMock(return_value=[_fake_user(1, "a", "a@x.com"),
                                                   _fake_user(2, "b", "b@x.com")])
            inst.count = AsyncMock(return_value=2)

            resp = await client.get("/api/v1/users/?page=1&per_page=20")

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] is True
        assert body["data"]["total"] == 2
        assert len(body["data"]["items"]) == 2

    @pytest.mark.anyio
    async def test_get_user_detail_success(self, client: AsyncClient):
        """Main flow: fetch a single user by id."""
        with patch("app.api.v1.users.UserRepository") as MockRepo:
            inst = MockRepo.return_value
            inst.get_by_id = AsyncMock(return_value=_fake_user(7, "seven", "7@x.com"))

            resp = await client.get("/api/v1/users/7")

        assert resp.status_code == 200
        assert resp.json()["data"]["username"] == "seven"

    @pytest.mark.anyio
    async def test_get_user_not_found_returns_404(self, client: AsyncClient):
        """Alt flow 5a: user detail not found -> 404."""
        with patch("app.api.v1.users.UserRepository") as MockRepo:
            inst = MockRepo.return_value
            inst.get_by_id = AsyncMock(return_value=None)

            resp = await client.get("/api/v1/users/999")

        assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_list_users_requires_auth(self, anon_client: AsyncClient):
        """Precondition: unauthenticated access -> 401/403."""
        resp = await anon_client.get("/api/v1/users/")
        # HTTPBearer returns 403 when the Authorization header is absent.
        assert resp.status_code in (401, 403)


# ═══════════════════════════════════════════════════════════════════
# UC-04  Manage Dataset
# ═══════════════════════════════════════════════════════════════════

class TestUC04ManageDataset:
    """UC-04: list/detail/delete datasets, list & search comments, imports."""

    @pytest.mark.anyio
    async def test_list_datasets_success(self, client: AsyncClient):
        """Main flow 1-2: list datasets with comment counts."""
        with (
            patch("app.api.v1.datasets.DatasetRepository") as MockDs,
            patch("app.api.v1.datasets.CommentRepository") as MockC,
        ):
            ds_inst = MockDs.return_value
            ds_inst.get_all = AsyncMock(return_value=[_dataset_obj(1), _dataset_obj(2)])
            ds_inst.count = AsyncMock(return_value=2)
            c_inst = MockC.return_value
            c_inst.count_by_dataset = AsyncMock(return_value=10)

            resp = await client.get("/api/v1/datasets/?page=1&per_page=20")

        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["total"] == 2
        assert body["data"]["items"][0]["comment_count"] == 10

    @pytest.mark.anyio
    async def test_get_dataset_detail_success(self, client: AsyncClient):
        """Main flow 3: open dataset detail with its comments."""
        with (
            patch("app.api.v1.datasets.DatasetRepository") as MockDs,
            patch("app.api.v1.datasets.CommentRepository") as MockC,
        ):
            MockDs.return_value.get_by_id = AsyncMock(return_value=_dataset_obj(1))
            c_inst = MockC.return_value
            c_inst.get_by_dataset = AsyncMock(return_value=[_comment_obj(1), _comment_obj(2)])
            c_inst.count_by_dataset = AsyncMock(return_value=2)

            resp = await client.get("/api/v1/datasets/1")

        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["id"] == 1
        assert len(body["data"]["comments"]) == 2

    @pytest.mark.anyio
    async def test_get_dataset_not_found_returns_404(self, client: AsyncClient):
        """Alt flow 3a: dataset not found -> 404."""
        with patch("app.api.v1.datasets.DatasetRepository") as MockDs:
            MockDs.return_value.get_by_id = AsyncMock(return_value=None)
            resp = await client.get("/api/v1/datasets/12345")
        assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_delete_dataset_success(self, client: AsyncClient):
        """Main flow 5: delete an existing dataset."""
        with patch("app.api.v1.datasets.DatasetRepository") as MockDs:
            MockDs.return_value.delete = AsyncMock(return_value=True)
            resp = await client.delete("/api/v1/datasets/1")
        assert resp.status_code == 200
        assert resp.json()["status"] is True

    @pytest.mark.anyio
    async def test_delete_dataset_not_found_returns_404(self, client: AsyncClient):
        """Alt flow 5a: deleting a missing dataset -> 404."""
        with patch("app.api.v1.datasets.DatasetRepository") as MockDs:
            MockDs.return_value.delete = AsyncMock(return_value=False)
            resp = await client.delete("/api/v1/datasets/999")
        assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_list_comments_success(self, client: AsyncClient):
        """Main flow 3: list comments of a dataset (paginated)."""
        with patch("app.api.v1.datasets.CommentRepository") as MockC:
            c_inst = MockC.return_value
            c_inst.get_by_dataset = AsyncMock(return_value=[_comment_obj(1)])
            c_inst.count_by_dataset = AsyncMock(return_value=1)
            resp = await client.get("/api/v1/datasets/1/comments?page=1&per_page=50")
        assert resp.status_code == 200
        assert resp.json()["data"]["total"] == 1

    @pytest.mark.anyio
    async def test_search_comments_success(self, client: AsyncClient):
        """Main flow 3: keyword search across comments."""
        with patch("app.api.v1.datasets.CommentRepository") as MockC:
            c_inst = MockC.return_value
            c_inst.search = AsyncMock(return_value=[_comment_obj(1)])
            c_inst.count_search = AsyncMock(return_value=1)
            resp = await client.get("/api/v1/datasets/search/comments?keyword=judi")
        assert resp.status_code == 200
        assert resp.json()["data"]["total"] == 1

    @pytest.mark.anyio
    async def test_search_comments_missing_keyword_returns_422(self, client: AsyncClient):
        """Validation: keyword is required."""
        resp = await client.get("/api/v1/datasets/search/comments")
        assert resp.status_code == 422

    # ----- Import sub-flows (UC-04 step 4) -----

    @pytest.mark.anyio
    async def test_import_youtube_success(self, client: AsyncClient):
        """Main flow 4: import YouTube comments -> creates dataset + comments."""
        fake_service = MagicMock()
        fake_service.fetch_comments = AsyncMock(return_value=[
            {"video_id": "vid123", "comment": "halo", "author": "a"},
        ])
        with (
            patch("app.api.v1.youtube.YouTubeService", return_value=fake_service),
            patch("app.api.v1.youtube.DatasetRepository") as MockDs,
            patch("app.api.v1.youtube.CommentRepository") as MockC,
        ):
            MockDs.return_value.create = AsyncMock(return_value=_dataset_obj(1))
            MockC.return_value.bulk_create = AsyncMock(return_value=1)

            resp = await client.post(
                "/api/v1/youtube/import",
                json={"video_id": "vid123", "dataset_name": "Test"},
            )

        assert resp.status_code == 200
        assert resp.json()["data"]["comment_count"] == 1

    @pytest.mark.anyio
    async def test_import_youtube_no_comments_returns_404(self, client: AsyncClient):
        """Alt flow 4a: no comments found -> 404."""
        fake_service = MagicMock()
        fake_service.fetch_comments = AsyncMock(return_value=[])
        with patch("app.api.v1.youtube.YouTubeService", return_value=fake_service):
            resp = await client.post(
                "/api/v1/youtube/import",
                json={"video_id": "vid123"},
            )
        assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_import_kaggle_success(self, client: AsyncClient):
        """Main flow 4: import a Kaggle dataset."""
        fake_service = MagicMock()
        fake_service.import_dataset = AsyncMock(return_value={
            "rows": [{"video_id": "x", "comment": "c"}],
            "columns_found": ["comment"],
            "source_url": "https://kaggle.com/x/y",
        })
        with (
            patch("app.api.v1.kaggle.KaggleService", return_value=fake_service),
            patch("app.api.v1.kaggle.DatasetRepository") as MockDs,
            patch("app.api.v1.kaggle.CommentRepository") as MockC,
        ):
            MockDs.return_value.create = AsyncMock(return_value=_dataset_obj(2))
            MockC.return_value.bulk_create = AsyncMock(return_value=1)

            resp = await client.post(
                "/api/v1/kaggle/import",
                json={"dataset_slug": "user/dataset"},
            )

        assert resp.status_code == 200
        assert resp.json()["data"]["comment_count"] == 1

    @pytest.mark.anyio
    async def test_import_kaggle_no_rows_returns_400(self, client: AsyncClient):
        """Alt flow 4a: no parseable rows -> 400."""
        fake_service = MagicMock()
        fake_service.import_dataset = AsyncMock(return_value={
            "rows": [],
            "columns_found": ["weird"],
            "source_url": "https://kaggle.com/x/y",
        })
        with patch("app.api.v1.kaggle.KaggleService", return_value=fake_service):
            resp = await client.post(
                "/api/v1/kaggle/import",
                json={"dataset_slug": "user/dataset"},
            )
        assert resp.status_code == 400

    @pytest.mark.anyio
    async def test_import_kaggle_requires_auth(self, anon_client: AsyncClient):
        """Precondition: import requires authentication."""
        resp = await anon_client.post(
            "/api/v1/kaggle/import", json={"dataset_slug": "user/dataset"}
        )
        assert resp.status_code in (401, 403)


# ═══════════════════════════════════════════════════════════════════
# UC-05  Predict Comments
# ═══════════════════════════════════════════════════════════════════

class TestUC05PredictComments:
    """UC-05: single/batch predict, auto-label dataset, manual correction."""

    @pytest.mark.anyio
    async def test_predict_single_success(self, client: AsyncClient):
        """Main flow 1-4: predict a single comment."""
        with patch("app.core.services.model_service.predict") as mock_predict:
            mock_predict.return_value = {
                "label": 1, "clean_comment": "slot gacor",
                "normal": 0.1, "judi": 0.9,
            }
            resp = await client.post(
                "/api/v1/labeling/predict", json={"text": "slot gacor"}
            )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["label"] == 1
        assert data["judi"] == 0.9

    @pytest.mark.anyio
    async def test_predict_single_model_error_returns_500(self, client: AsyncClient):
        """Alt flow 3a: model fails to load -> 500."""
        with patch("app.core.services.model_service.predict",
                   side_effect=RuntimeError("model missing")):
            resp = await client.post(
                "/api/v1/labeling/predict", json={"text": "halo"}
            )
        assert resp.status_code == 500

    @pytest.mark.anyio
    async def test_predict_batch_success(self, client: AsyncClient):
        """Main flow: batch prediction returns one result per text."""
        with patch("app.core.services.model_service.predict_batch") as mock_pb:
            mock_pb.return_value = [
                {"label": 0, "clean_comment": "a", "normal": 0.8, "judi": 0.2},
                {"label": 1, "clean_comment": "b", "normal": 0.2, "judi": 0.8},
            ]
            resp = await client.post(
                "/api/v1/labeling/predict/batch",
                json={"texts": ["a", "b"]},
            )
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 2

    @pytest.mark.anyio
    async def test_auto_label_dataset_success(self, client: AsyncClient, fake_db):
        """Main flow: auto-label all comments in a dataset."""
        result = MagicMock()
        result.scalars.return_value.all.return_value = [
            _comment_obj(1), _comment_obj(2),
        ]
        fake_db.execute = AsyncMock(return_value=result)

        with patch("app.core.services.model_service.predict_batch") as mock_pb:
            mock_pb.return_value = [
                {"label": 1, "clean_comment": "x", "normal": 0.1, "judi": 0.9},
                {"label": 0, "clean_comment": "y", "normal": 0.9, "judi": 0.1},
            ]
            resp = await client.post("/api/v1/labeling/dataset/1")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total_comments"] == 2
        assert data["judi_count"] == 1
        assert data["normal_count"] == 1

    @pytest.mark.anyio
    async def test_auto_label_dataset_no_comments_returns_404(self, client: AsyncClient, fake_db):
        """Alt flow 1a: dataset has no comments -> 404."""
        result = MagicMock()
        result.scalars.return_value.all.return_value = []
        fake_db.execute = AsyncMock(return_value=result)

        resp = await client.post("/api/v1/labeling/dataset/999")
        assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_manual_label_comment_success(self, client: AsyncClient):
        """Main flow 5: manually correct a comment label."""
        with patch("app.api.v1.labeling.CommentRepository") as MockC:
            MockC.return_value.update_label = AsyncMock(
                return_value=_comment_obj(1, label="1")
            )
            resp = await client.patch(
                "/api/v1/labeling/comment/1", json={"label": "1"}
            )
        assert resp.status_code == 200
        assert resp.json()["data"]["label"] == "1"

    @pytest.mark.anyio
    async def test_manual_label_comment_not_found_returns_404(self, client: AsyncClient):
        """Alt flow 5a: comment not found -> 404."""
        with patch("app.api.v1.labeling.CommentRepository") as MockC:
            MockC.return_value.update_label = AsyncMock(return_value=None)
            resp = await client.patch(
                "/api/v1/labeling/comment/999", json={"label": "0"}
            )
        assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_manual_label_invalid_value_returns_422(self, client: AsyncClient):
        """Validation: label must be '0' or '1'."""
        resp = await client.patch(
            "/api/v1/labeling/comment/1", json={"label": "2"}
        )
        assert resp.status_code == 422

    @pytest.mark.anyio
    async def test_reset_manual_label_success(self, client: AsyncClient):
        """Main flow: reset manual label back to null."""
        with patch("app.api.v1.labeling.CommentRepository") as MockC:
            MockC.return_value.update_label = AsyncMock(
                return_value=_comment_obj(1, label=None)
            )
            resp = await client.delete("/api/v1/labeling/comment/1/label")
        assert resp.status_code == 200

    @pytest.mark.anyio
    async def test_bulk_manual_label_success(self, client: AsyncClient, fake_db):
        """Main flow: bulk-correct labels, skipping ids outside the dataset."""
        # Only comment id 1 belongs to dataset 1
        result = MagicMock()
        result.all.return_value = [(1,)]
        fake_db.execute = AsyncMock(return_value=result)

        with patch("app.api.v1.labeling.CommentRepository") as MockC:
            MockC.return_value.bulk_update_labels = AsyncMock(return_value=1)
            resp = await client.patch(
                "/api/v1/labeling/dataset/1/bulk",
                json={"labels": [
                    {"comment_id": 1, "label": "1"},
                    {"comment_id": 2, "label": "0"},  # not in dataset -> skipped
                ]},
            )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["updated_count"] == 1
        assert data["skipped_count"] == 1

    @pytest.mark.anyio
    async def test_predict_requires_auth_on_dataset_label(self, anon_client: AsyncClient):
        """Precondition: auto-label requires authentication."""
        resp = await anon_client.post("/api/v1/labeling/dataset/1")
        assert resp.status_code in (401, 403)


# ═══════════════════════════════════════════════════════════════════
# UC-06  Manage Cookie YouTube Accounts
# ═══════════════════════════════════════════════════════════════════

class TestUC06ManageCookieAccounts:
    """UC-06: list/detail/delete cookie accounts + Google login (SSE)."""

    @pytest.mark.anyio
    async def test_list_cookies_success(self, client: AsyncClient):
        """Main flow 5: list stored cookie accounts."""
        acc = SimpleNamespace(
            id=1, email="a@gmail.com", channel_name="Chan",
            cookie_path="cookies/a/youtube_cookies.json", cookie_count=10,
            is_active=1, created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )
        with (
            patch("app.api.v1.auto_delete.CookieAccountRepository") as MockRepo,
            patch("app.core.services.cookie_manager.CookieManager") as MockMgr,
        ):
            MockRepo.return_value.get_all = AsyncMock(return_value=[acc])
            MockMgr.return_value.exists.return_value = True

            resp = await client.get("/api/v1/auto-delete/cookies")

        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["total"] == 1
        assert body["data"]["accounts"][0]["email"] == "a@gmail.com"

    @pytest.mark.anyio
    async def test_get_cookie_detail_success(self, client: AsyncClient):
        """Main flow 5: get details for one cookie account."""
        acc = SimpleNamespace(
            id=1, email="a@gmail.com", channel_name="Chan",
            cookie_path="cookies/a/youtube_cookies.json", cookie_count=10,
            is_active=1, created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )
        with (
            patch("app.api.v1.auto_delete.CookieAccountRepository") as MockRepo,
            patch("app.core.services.cookie_manager.CookieManager") as MockMgr,
        ):
            MockRepo.return_value.get_by_email = AsyncMock(return_value=acc)
            MockMgr.return_value.get_cookie_info.return_value = {"count": 10}

            resp = await client.get("/api/v1/auto-delete/cookies/a@gmail.com")

        assert resp.status_code == 200
        assert resp.json()["data"]["email"] == "a@gmail.com"

    @pytest.mark.anyio
    async def test_get_cookie_detail_not_found(self, client: AsyncClient):
        """Alt flow 5a: cookie not found -> error response (status False)."""
        with patch("app.api.v1.auto_delete.CookieAccountRepository") as MockRepo:
            MockRepo.return_value.get_by_email = AsyncMock(return_value=None)
            resp = await client.get("/api/v1/auto-delete/cookies/missing@gmail.com")
        assert resp.status_code == 200
        assert resp.json()["status"] is False

    @pytest.mark.anyio
    async def test_delete_cookie_success(self, client: AsyncClient):
        """Main flow 5: delete a cookie account (file + db)."""
        acc = SimpleNamespace(
            id=1, email="a@gmail.com",
            cookie_path="cookies/a/youtube_cookies.json",
        )
        with (
            patch("app.api.v1.auto_delete.CookieAccountRepository") as MockRepo,
            patch("app.core.services.cookie_manager.CookieManager") as MockMgr,
        ):
            MockRepo.return_value.get_by_email = AsyncMock(return_value=acc)
            MockRepo.return_value.delete_by_email = AsyncMock(return_value=True)
            MockMgr.return_value.delete.return_value = True

            resp = await client.delete("/api/v1/auto-delete/cookies/a@gmail.com")

        assert resp.status_code == 200
        assert resp.json()["data"]["db_deleted"] is True

    @pytest.mark.anyio
    async def test_delete_cookie_not_found(self, client: AsyncClient):
        """Alt flow 5a: deleting a missing cookie -> error response."""
        with patch("app.api.v1.auto_delete.CookieAccountRepository") as MockRepo:
            MockRepo.return_value.get_by_email = AsyncMock(return_value=None)
            resp = await client.delete("/api/v1/auto-delete/cookies/missing@gmail.com")
        assert resp.status_code == 200
        assert resp.json()["status"] is False

    @pytest.mark.anyio
    async def test_google_login_streams_sse(self, client: AsyncClient):
        """Main flow 1-4: Google login returns an SSE event-stream."""
        def _fake_login_stream(**kwargs):
            yield 'event: status\ndata: {"message": "Memulai browser..."}\n\n'
            yield 'event: done\ndata: {"logged_in": true}\n\n'

        with patch(
            "app.core.services.auto_delete_service.AutoDeleteService.login_stream",
            side_effect=_fake_login_stream,
        ):
            resp = await client.post(
                "/api/v1/auto-delete/login",
                json={"email": "a@gmail.com", "password": "secret"},
            )

        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")
        assert "logged_in" in resp.text

    @pytest.mark.anyio
    async def test_cookies_requires_auth(self, anon_client: AsyncClient):
        """Precondition: cookie management requires authentication."""
        resp = await anon_client.get("/api/v1/auto-delete/cookies")
        assert resp.status_code in (401, 403)


# ═══════════════════════════════════════════════════════════════════
# UC-07  Delete Gambling Comments
# ═══════════════════════════════════════════════════════════════════

class TestUC07DeleteGamblingComments:
    """UC-07: scan & delete, preview (dry-run), delete specific, fetch comments."""

    @pytest.mark.anyio
    async def test_scan_and_delete_streams_sse(self, client: AsyncClient):
        """Main flow: scan+delete returns an SSE stream with a 'done' event."""
        fake_service = MagicMock()
        fake_service.start_browser.return_value = True
        fake_service.scan_video_stream.return_value = iter([
            'event: done\ndata: {"deleted": 2}\n\n',
        ])
        fake_service.stop_browser.return_value = None

        with patch(
            "app.core.services.auto_delete_service.AutoDeleteService",
            return_value=fake_service,
        ):
            resp = await client.post(
                "/api/v1/auto-delete/scan",
                json={"video_id": "vid123", "email": "a@gmail.com", "threshold": 0.7},
            )

        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")
        assert "done" in resp.text

    @pytest.mark.anyio
    async def test_scan_browser_failure_emits_error_event(self, client: AsyncClient):
        """Alt flow 2a: cookie missing / browser fails -> SSE 'error' event."""
        fake_service = MagicMock()
        fake_service.start_browser.return_value = False
        fake_service.stop_browser.return_value = None

        with patch(
            "app.core.services.auto_delete_service.AutoDeleteService",
            return_value=fake_service,
        ):
            resp = await client.post(
                "/api/v1/auto-delete/scan",
                json={"video_id": "vid123", "email": "missing@gmail.com"},
            )

        assert resp.status_code == 200
        assert "event: error" in resp.text

    @pytest.mark.anyio
    async def test_scan_preview_dry_run_streams_sse(self, client: AsyncClient):
        """Alt flow (preview): dry-run scan returns an SSE stream."""
        fake_service = MagicMock()
        fake_service.start_browser.return_value = True
        fake_service.scan_video_stream.return_value = iter([
            'event: done\ndata: {"dry_run": true}\n\n',
        ])
        fake_service.stop_browser.return_value = None

        with patch(
            "app.core.services.auto_delete_service.AutoDeleteService",
            return_value=fake_service,
        ):
            resp = await client.post(
                "/api/v1/auto-delete/scan/preview",
                json={"video_id": "vid123", "email": "a@gmail.com"},
            )

        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")

    @pytest.mark.anyio
    async def test_delete_specific_comments_streams_sse(self, client: AsyncClient):
        """Alt flow (delete specific): delete by comment_ids."""
        fake_service = MagicMock()
        fake_service.start_browser.return_value = True
        fake_service.delete_specific_comments.return_value = 2
        fake_service.stop_browser.return_value = None

        with patch(
            "app.core.services.auto_delete_service.AutoDeleteService",
            return_value=fake_service,
        ):
            resp = await client.post(
                "/api/v1/auto-delete/delete",
                json={
                    "video_id": "vid123",
                    "email": "a@gmail.com",
                    "comment_ids": ["c1", "c2"],
                },
            )

        assert resp.status_code == 200
        assert "done" in resp.text

    @pytest.mark.anyio
    async def test_fetch_comments_streams_sse(self, client: AsyncClient):
        """Main flow: fetch raw comments (no ML) as SSE."""
        fake_service = MagicMock()
        fake_service.start_browser.return_value = True
        fake_service.fetch_video_comments.return_value = [
            {"comment_id": "c1", "comment": "halo"},
        ]
        fake_service.stop_browser.return_value = None

        with patch(
            "app.core.services.auto_delete_service.AutoDeleteService",
            return_value=fake_service,
        ):
            resp = await client.post(
                "/api/v1/auto-delete/comments",
                json={"video_id": "vid123", "email": "a@gmail.com"},
            )

        assert resp.status_code == 200
        assert "done" in resp.text

    @pytest.mark.anyio
    async def test_delete_requires_comment_ids(self, client: AsyncClient):
        """Validation: comment_ids must be non-empty."""
        resp = await client.post(
            "/api/v1/auto-delete/delete",
            json={"video_id": "vid123", "email": "a@gmail.com", "comment_ids": []},
        )
        assert resp.status_code == 422

    @pytest.mark.anyio
    async def test_scan_requires_auth(self, anon_client: AsyncClient):
        """Precondition: scan requires authentication."""
        resp = await anon_client.post(
            "/api/v1/auto-delete/scan",
            json={"video_id": "vid123", "email": "a@gmail.com"},
        )
        assert resp.status_code in (401, 403)


# ═══════════════════════════════════════════════════════════════════
# UC-08  Explore Video
# ═══════════════════════════════════════════════════════════════════

class TestUC08ExploreVideo:
    """UC-08: explore a single video via SSE (scan-only and save modes)."""

    @pytest.mark.anyio
    async def test_explore_video_scan_only(self, client: AsyncClient):
        """Alt flow 4b: no dataset_name -> scan-only, not saved."""
        async def _fake_stream(video_id):
            yield {"type": "fetch_comments_done", "total": 5}
            yield {
                "type": "done",
                "comments": [{"video_id": video_id, "comment": "slot", "predicted_label": "1"}],
                "stats": {"video_id": video_id, "title": "T", "total_judi": 1},
                "message": "done",
            }

        with patch(
            "app.core.services.explorer_service.explore_video_stream",
            side_effect=_fake_stream,
        ):
            resp = await client.post(
                "/api/v1/explorer/run", json={"video_id": "vid123"}
            )

        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")
        assert "event: complete" in resp.text
        # Scan-only message indicates nothing was saved
        assert "Scan only" in resp.text or '"saved": false' in resp.text.lower() or '"saved": False' in resp.text

    @pytest.mark.anyio
    async def test_explore_video_saves_when_dataset_name_given(self, client: AsyncClient):
        """Main flow 4: judi found + dataset_name -> saved to DB."""
        async def _fake_stream(video_id):
            yield {
                "type": "done",
                "comments": [{"video_id": video_id, "comment": "slot", "predicted_label": "1"}],
                "stats": {"video_id": video_id, "title": "T", "total_judi": 1,
                          "total_normal": 0, "total_saved": 1, "total_fetched": 1,
                          "judi_percentage": 100},
                "message": "done",
            }

        with (
            patch("app.core.services.explorer_service.explore_video_stream",
                  side_effect=_fake_stream),
            patch("app.api.v1.explorer.DatasetRepository") as MockDs,
            patch("app.api.v1.explorer.CommentRepository") as MockC,
        ):
            MockDs.return_value.create = AsyncMock(return_value=_dataset_obj(5))
            MockC.return_value.bulk_create = AsyncMock(return_value=1)

            resp = await client.post(
                "/api/v1/explorer/run",
                json={"video_id": "vid123", "dataset_name": "My Explore"},
            )

        assert resp.status_code == 200
        assert "event: complete" in resp.text
        assert "Tersimpan" in resp.text

    @pytest.mark.anyio
    async def test_explore_video_no_judi_not_saved(self, client: AsyncClient):
        """Alt flow 4a: 0 judi -> not saved."""
        async def _fake_stream(video_id):
            yield {
                "type": "done",
                "comments": [],
                "stats": {"video_id": video_id, "total_judi": 0},
                "message": "Tidak ada judi",
            }

        with patch(
            "app.core.services.explorer_service.explore_video_stream",
            side_effect=_fake_stream,
        ):
            resp = await client.post(
                "/api/v1/explorer/run",
                json={"video_id": "vid123", "dataset_name": "X"},
            )

        assert resp.status_code == 200
        assert "event: complete" in resp.text

    @pytest.mark.anyio
    async def test_explore_video_requires_auth(self, anon_client: AsyncClient):
        """Precondition: explore requires authentication."""
        resp = await anon_client.post(
            "/api/v1/explorer/run", json={"video_id": "vid123"}
        )
        assert resp.status_code in (401, 403)

    @pytest.mark.anyio
    async def test_explore_video_missing_video_id_returns_422(self, client: AsyncClient):
        """Validation: video_id is required."""
        resp = await client.post("/api/v1/explorer/run", json={})
        assert resp.status_code == 422


# ═══════════════════════════════════════════════════════════════════
# UC-09  Explore Channel
# ═══════════════════════════════════════════════════════════════════

class TestUC09ExploreChannel:
    """UC-09: explore a channel via SSE (scan-only and save modes)."""

    @pytest.mark.anyio
    async def test_explore_channel_scan_only(self, client: AsyncClient):
        """Alt flow 5a: no dataset_name -> scan-only, video_saved with count 0."""
        async def _fake_stream(channel_input, max_videos):
            yield {"type": "channel_info", "channel_name": "Chan", "channel_id": "ch1"}
            yield {
                "type": "video_ready",
                "video_id": "v1", "title": "Vid 1",
                "channel_id": "ch1", "channel_name": "Chan",
                "video_judi": 2, "video_normal": 3,
                "comments": [{"video_id": "v1", "comment": "slot"}],
            }
            yield {"type": "done", "stats": {"total_judi": 2}, "message": "selesai"}

        with patch(
            "app.core.services.channel_explorer_service.explore_channel_stream",
            side_effect=_fake_stream,
        ):
            resp = await client.post(
                "/api/v1/explorer/channel/run",
                json={"channel": "@chan", "max_videos": 5},
            )

        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")
        assert "event: complete" in resp.text
        assert "Scan only" in resp.text

    @pytest.mark.anyio
    async def test_explore_channel_saves_when_dataset_name_given(self, client: AsyncClient):
        """Main flow 5: video with judi + dataset_name -> saved."""
        async def _fake_stream(channel_input, max_videos):
            yield {
                "type": "video_ready",
                "video_id": "v1", "title": "Vid 1",
                "channel_id": "ch1", "channel_name": "Chan",
                "video_judi": 2, "video_normal": 3,
                "comments": [{"video_id": "v1", "comment": "slot"}],
            }
            yield {"type": "done", "stats": {"total_judi": 2}, "message": "selesai"}

        with (
            patch("app.core.services.channel_explorer_service.explore_channel_stream",
                  side_effect=_fake_stream),
            patch("app.api.v1.channel_explorer.DatasetRepository") as MockDs,
            patch("app.api.v1.channel_explorer.CommentRepository") as MockC,
        ):
            MockDs.return_value.create = AsyncMock(return_value=_dataset_obj(9))
            MockC.return_value.bulk_create = AsyncMock(return_value=1)

            resp = await client.post(
                "/api/v1/explorer/channel/run",
                json={"channel": "@chan", "max_videos": 5, "dataset_name": "Chan DS"},
            )

        assert resp.status_code == 200
        assert "event: complete" in resp.text
        assert "Tersimpan" in resp.text

    @pytest.mark.anyio
    async def test_explore_channel_requires_auth(self, anon_client: AsyncClient):
        """Precondition: channel explore requires authentication."""
        resp = await anon_client.post(
            "/api/v1/explorer/channel/run", json={"channel": "@chan"}
        )
        assert resp.status_code in (401, 403)

    @pytest.mark.anyio
    async def test_explore_channel_missing_channel_returns_422(self, client: AsyncClient):
        """Validation: channel is required."""
        resp = await client.post("/api/v1/explorer/channel/run", json={})
        assert resp.status_code == 422
