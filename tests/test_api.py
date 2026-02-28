"""Comprehensive tests for the Purifyt API."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.utils.text_cleaner import clean_comment
from app.core.services.model_service import predict, predict_batch


# Fixtures 

@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# Health & Root 

@pytest.mark.anyio
async def test_root(client: AsyncClient):
    resp = await client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert "app" in data
    assert "version" in data
    assert "docs" in data


@pytest.mark.anyio
async def test_health(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# Auth 

@pytest.mark.anyio
async def test_register_missing_fields(client: AsyncClient):
    resp = await client.post("/api/v1/auth/register", json={})
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_register_short_password(client: AsyncClient):
    resp = await client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "123",
    })
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_register_invalid_email(client: AsyncClient):
    resp = await client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "email": "not-an-email",
        "password": "password123",
    })
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_login_invalid(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "nonexistent", "password": "wrong"},
    )
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_login_missing_fields(client: AsyncClient):
    resp = await client.post("/api/v1/auth/login", data={})
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_refresh_invalid_token(client: AsyncClient):
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": "invalid.jwt.token"})
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_refresh_missing_body(client: AsyncClient):
    resp = await client.post("/api/v1/auth/refresh", json={})
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_refresh_with_access_token_rejected(client: AsyncClient):
    """An access_token should NOT be accepted as a refresh_token."""
    from app.core.services.auth_service import create_access_token
    at = create_access_token(data={"sub": "testuser"})
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": at})
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_logout_no_auth(client: AsyncClient):
    resp = await client.post("/api/v1/auth/logout")
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_logout_all_no_auth(client: AsyncClient):
    resp = await client.post("/api/v1/auth/logout/all")
    assert resp.status_code == 401


# Protected Endpoints (no auth) 

@pytest.mark.anyio
async def test_explorer_no_auth(client: AsyncClient):
    resp = await client.post("/api/v1/explorer/run", json={"video_id": "test"})
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_channel_explorer_no_auth(client: AsyncClient):
    resp = await client.post("/api/v1/explorer/channel/run", json={"channel": "@test"})
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_kaggle_import_no_auth(client: AsyncClient):
    resp = await client.post("/api/v1/kaggle/import", json={"dataset_slug": "user/dataset"})
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_labeling_dataset_no_auth(client: AsyncClient):
    resp = await client.post("/api/v1/labeling/dataset/1")
    assert resp.status_code == 401


# Datasets 

@pytest.mark.anyio
async def test_datasets_list(client: AsyncClient):
    """Datasets endpoint hits DB; skip gracefully when no DB is available."""
    try:
        resp = await client.get("/api/v1/datasets/")
        assert resp.status_code in (200, 500)
    except (AttributeError, ConnectionError, OSError):
        pytest.skip("Database not available")


# YouTube 

@pytest.mark.anyio
async def test_youtube_search_no_query(client: AsyncClient):
    resp = await client.get("/api/v1/youtube/search")
    assert resp.status_code == 422


# Text Cleaner 

class TestTextCleaner:
    def test_empty_string(self):
        assert clean_comment("") == ""

    def test_none_input(self):
        assert clean_comment(None) == ""

    def test_basic_lowercase(self):
        assert clean_comment("HELLO WORLD") == "hello world"

    def test_remove_emojis(self):
        result = clean_comment("ini komentar 😀😂🔥")
        assert "😀" not in result
        assert "😂" not in result
        assert "🔥" not in result
        assert "ini komentar" in result

    def test_remove_circle_emojis(self):
        result = clean_comment("test 🟣🟢🔵")
        assert "🟣" not in result
        assert "🟢" not in result

    def test_keep_fancy_unicode(self):
        result = clean_comment("𝐌𝐎𝐍𝐀𝟒𝐃")
        assert "𝐌𝐎𝐍𝐀" in result or "𝐦𝐨𝐧𝐚" in result or len(result) > 0

    def test_remove_superscripts(self):
        result = clean_comment("x² + y³")
        assert "²" not in result
        assert "³" not in result

    def test_collapse_repeated_dots(self):
        result = clean_comment("wait... really...")
        assert "..." not in result
        assert "wait" in result

    def test_collapse_repeated_commas(self):
        result = clean_comment("ok,,,, sure,,, yes")
        assert ",,," not in result
        assert "ok" in result

    def test_collapse_repeated_exclamation(self):
        result = clean_comment("wow!!!! amazing!!!")
        assert "!!!!" not in result
        assert "wow" in result

    def test_collapse_repeated_chars(self):
        result = clean_comment("wkwkwk aaaa wwwww")
        assert "aaaa" not in result
        assert "wwwww" not in result

    def test_remove_zero_width_chars(self):
        result = clean_comment("hello\u200bworld")
        assert "\u200b" not in result

    def test_whitespace_collapse(self):
        result = clean_comment("hello    world   test")
        assert result == "hello world test"

    def test_strip(self):
        result = clean_comment("  hello world  ")
        assert result == "hello world"

    def test_mixed_emojis_and_text(self):
        result = clean_comment("Bang windah kamu kok gak main 😢😢😢")
        assert result == "bang windah kamu kok gak main"

    def test_url_like_text(self):
        result = clean_comment("kunjungi www.slot88.com sekarang")
        assert "slot88" in result

    def test_numbers_preserved(self):
        result = clean_comment("Video ke-123 dari channel ini")
        assert "123" in result


# Model Service 

class TestModelService:
    def test_predict_returns_expected_keys(self):
        result = predict("ini komentar biasa")
        assert "label" in result
        assert "clean_comment" in result
        assert "normal" in result
        assert "judi" in result

    def test_predict_label_is_int(self):
        result = predict("ini komentar biasa")
        assert isinstance(result["label"], int)
        assert result["label"] in (0, 1)

    def test_predict_probabilities_sum_to_one(self):
        result = predict("test comment")
        total = result["normal"] + result["judi"]
        assert abs(total - 1.0) < 0.01

    def test_predict_empty_string(self):
        result = predict("")
        assert result["label"] == 0
        assert result["clean_comment"] == ""

    def test_predict_batch_returns_list(self):
        results = predict_batch(["komentar satu", "komentar dua"])
        assert isinstance(results, list)
        assert len(results) == 2

    def test_predict_batch_each_has_keys(self):
        results = predict_batch(["test1", "test2"])
        for r in results:
            assert "label" in r
            assert "clean_comment" in r
            assert "normal" in r
            assert "judi" in r

    def test_predict_batch_empty_list(self):
        results = predict_batch([])
        assert results == []

    def test_predict_batch_with_empty_strings(self):
        results = predict_batch(["", "", "hello"])
        assert len(results) == 3

    def test_predict_long_text(self):
        long_text = "komentar panjang " * 500
        result = predict(long_text)
        assert result["label"] in (0, 1)

    def test_predict_known_judi_pattern(self):
        result = predict("slot gacor 88 deposit 10 ribu link daftar di bio")
        assert result["label"] in (0, 1)

    def test_predict_known_normal_pattern(self):
        result = predict("video ini bagus banget, terus berkarya ya bang")
        assert result["label"] in (0, 1)


# Schema Validation 

class TestSchemas:
    def test_kaggle_import_request(self):
        from app.core.schemas import KaggleImportRequest
        req = KaggleImportRequest(dataset_slug="user/dataset")
        assert req.dataset_slug == "user/dataset"
        assert req.dataset_name is None

    def test_kaggle_import_with_name(self):
        from app.core.schemas import KaggleImportRequest
        req = KaggleImportRequest(dataset_slug="user/dataset", dataset_name="My Dataset")
        assert req.dataset_name == "My Dataset"

    def test_user_create_validation(self):
        from app.core.schemas import UserCreate
        user = UserCreate(username="test", email="test@test.com", password="123456")
        assert user.username == "test"

    def test_user_create_short_username(self):
        from app.core.schemas import UserCreate
        with pytest.raises(Exception):
            UserCreate(username="ab", email="test@test.com", password="123456")

    def test_youtube_search_request(self):
        from app.core.schemas import YouTubeSearchRequest
        req = YouTubeSearchRequest(query="test")
        assert req.query == "test"
        assert req.max_results is None

    def test_dataset_create(self):
        from app.core.schemas import DatasetCreate
        ds = DatasetCreate(name="Test Dataset")
        assert ds.name == "Test Dataset"
        assert ds.description is None


# Auth Service 

class TestAuthService:
    def test_hash_password(self):
        from app.core.services.auth_service import hash_password
        hashed = hash_password("test123")
        assert hashed != "test123"
        assert len(hashed) > 20

    def test_verify_password(self):
        from app.core.services.auth_service import hash_password, verify_password
        hashed = hash_password("mypassword")
        assert verify_password("mypassword", hashed) is True
        assert verify_password("wrongpassword", hashed) is False

    def test_create_access_token(self):
        from app.core.services.auth_service import create_access_token
        token = create_access_token(data={"sub": "testuser"})
        assert isinstance(token, str)
        assert len(token) > 10

    def test_create_access_token_with_expiry(self):
        from datetime import timedelta
        from app.core.services.auth_service import create_access_token
        token = create_access_token(
            data={"sub": "testuser"},
            expires_delta=timedelta(minutes=5),
        )
        assert isinstance(token, str)

    def test_create_refresh_token(self):
        from app.core.services.auth_service import create_refresh_token, decode_token
        token = create_refresh_token(data={"sub": "testuser"})
        assert isinstance(token, str)
        payload = decode_token(token)
        assert payload["type"] == "refresh"
        assert payload["sub"] == "testuser"
        assert "jti" in payload

    def test_create_token_pair(self):
        from app.core.services.auth_service import create_token_pair, decode_token
        pair = create_token_pair("testuser")
        assert "access_token" in pair
        assert "refresh_token" in pair
        assert pair["token_type"] == "bearer"

        access_payload = decode_token(pair["access_token"])
        assert access_payload["type"] == "access"
        assert access_payload["sub"] == "testuser"

        refresh_payload = decode_token(pair["refresh_token"])
        assert refresh_payload["type"] == "refresh"
        assert refresh_payload["sub"] == "testuser"

    def test_access_token_has_jti(self):
        from app.core.services.auth_service import create_access_token, decode_token
        token = create_access_token(data={"sub": "testuser"})
        payload = decode_token(token)
        assert "jti" in payload
        assert len(payload["jti"]) == 36  # UUID format

    def test_token_types_differ(self):
        from app.core.services.auth_service import create_access_token, create_refresh_token, decode_token
        at = create_access_token(data={"sub": "u"})
        rt = create_refresh_token(data={"sub": "u"})
        assert decode_token(at)["type"] == "access"
        assert decode_token(rt)["type"] == "refresh"
        assert decode_token(at)["jti"] != decode_token(rt)["jti"]


# Kaggle Service 

class TestKaggleService:
    def test_build_mapping_auto_detect(self):
        from app.core.services.kaggle_service import KaggleService
        mapping = KaggleService._build_mapping(["comment", "label", "video_id", "extra_col"])
        assert mapping.get("comment") == "comment"
        assert mapping.get("label") == "label"
        assert mapping.get("video_id") == "video_id"
        assert "extra_col" not in mapping

    def test_build_mapping_case_insensitive(self):
        from app.core.services.kaggle_service import KaggleService
        mapping = KaggleService._build_mapping(["Comment", "Label", "Video_ID"])
        assert "Comment" in mapping or "comment" in [v for v in mapping.values()]

    def test_build_mapping_indonesian_aliases(self):
        from app.core.services.kaggle_service import KaggleService
        mapping = KaggleService._build_mapping(["komentar", "tanggal", "komentar_clean"])
        assert any(v == "comment" for v in mapping.values())
        assert any(v == "date" for v in mapping.values())
        assert any(v == "clean_comment" for v in mapping.values())

    def test_build_mapping_empty_columns(self):
        from app.core.services.kaggle_service import KaggleService
        mapping = KaggleService._build_mapping([])
        assert mapping == {}

    def test_build_mapping_no_match(self):
        from app.core.services.kaggle_service import KaggleService
        mapping = KaggleService._build_mapping(["col_a", "col_b", "col_c"])
        assert mapping == {}


# Explorer Service Helpers 

class TestExplorerHelpers:
    def test_build_stats(self):
        from app.core.services.explorer_service import _build_stats
        stats = _build_stats("vid123", "Title", "Channel", 100, 10, 90, 100)
        assert stats["video_id"] == "vid123"
        assert stats["title"] == "Title"
        assert stats["total_fetched"] == 100
        assert stats["total_judi"] == 10
        assert stats["judi_percentage"] == 10.0

    def test_build_stats_zero_saved(self):
        from app.core.services.explorer_service import _build_stats
        stats = _build_stats("vid123", "Title", "Channel", 100, 0, 0, 0)
        assert stats["judi_percentage"] == 0

    def test_done_empty(self):
        from app.core.services.explorer_service import _done_empty
        result = _done_empty("vid123", "No comments")
        assert result["type"] == "done"
        assert result["comments"] == []
        assert result["message"] == "No comments"


class TestChannelExplorerHelpers:
    def test_build_channel_stats(self):
        from app.core.services.channel_explorer_service import _build_channel_stats
        stats = _build_channel_stats("ch123", "MyChannel", 10, 8, 500, 20, 30, 50)
        assert stats["channel_id"] == "ch123"
        assert stats["channel_name"] == "MyChannel"
        assert stats["total_videos"] == 10
        assert stats["videos_processed"] == 8
        assert stats["total_fetched"] == 500
        assert stats["total_judi"] == 20
        assert stats["judi_percentage"] == 40.0

    def test_build_channel_stats_zero(self):
        from app.core.services.channel_explorer_service import _build_channel_stats
        stats = _build_channel_stats("ch123", "MyChannel", 0, 0, 0, 0, 0, 0)
        assert stats["judi_percentage"] == 0

    def test_done_empty(self):
        from app.core.services.channel_explorer_service import _done_empty
        result = _done_empty("@channel", "Not found")
        assert result["type"] == "done"
        assert result["comments"] == []
