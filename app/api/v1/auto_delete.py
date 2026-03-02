from typing import Optional, List

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.logging_config import get_logger
from app.db.connection import get_db
from app.db.repositories.cookie_account_repository import CookieAccountRepository
from app.utils.response_formatter import APIResponse, success_response, error_response

logger = get_logger(__name__)

router = APIRouter(prefix="/auto-delete", tags=["Auto Delete"])

_SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


def _sse_response(generator) -> StreamingResponse:
    """Helper to create a StreamingResponse in SSE format."""
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers=_SSE_HEADERS,
    )


# Request Schemas 
class LoginRequest(BaseModel):
    email: str = Field(..., description="Email akun Google")
    password: str = Field(..., description="Password akun Google")
    headless: bool = Field(
        default=True,
        description="Jalankan browser tanpa GUI (default True, auto-login)",
    )
    timeout: int = Field(
        default=120, ge=30, le=600,
        description="Timeout login dalam detik (default 2 menit)",
    )


class ScanRequest(BaseModel):
    video_id: str = Field(..., description="YouTube video ID")
    email: str = Field(..., description="Email akun Google yang cookienya akan dipakai")
    threshold: float = Field(
        default=0.7, ge=0.0, le=1.0,
        description="Threshold confidence deteksi judi (0.0-1.0)",
    )
    headless: bool = Field(
        default=True,
        description="Jalankan browser tanpa GUI",
    )


class DeleteRequest(BaseModel):
    video_id: str = Field(..., description="YouTube video ID")
    email: str = Field(..., description="Email akun Google yang cookienya akan dipakai")
    comment_ids: List[str] = Field(
        ..., min_length=1,
        description="List comment IDs yang mau dihapus",
    )
    headless: bool = Field(default=True)


class FetchCommentsRequest(BaseModel):
    video_id: str = Field(..., description="YouTube video ID")
    email: str = Field(..., description="Email akun Google yang cookienya akan dipakai")
    headless: bool = Field(default=True)


# SSE Stream Generators 
def _run_scan_stream(payload: ScanRequest, dry_run: bool):
    """Generator: scan video → yield SSE events."""
    from app.core.services.auto_delete_service import AutoDeleteService, _sse_event

    service = AutoDeleteService(
        email=payload.email,
        threshold=payload.threshold,
        headless=payload.headless,
    )

    try:
        yield _sse_event("status", {"step": "browser", "message": "Memulai browser..."})

        if not service.start_browser():
            yield _sse_event("error", {
                "message": f"Gagal start browser. Cookie untuk {payload.email} tidak ditemukan. Login dulu via POST /auto-delete/login."
            })
            return

        yield _sse_event("status", {"step": "browser", "message": "Browser siap ✓"})

        yield from service.scan_video_stream(
            video_id=payload.video_id,
            dry_run=dry_run,
        )

    except Exception as e:
        logger.error(f"Scan stream error: {e}", exc_info=True)
        yield _sse_event("error", {"message": str(e)})
    finally:
        service.stop_browser()


def _run_delete_stream(payload: DeleteRequest):
    """Generator: delete specific comments → yield SSE events."""
    from app.core.services.auto_delete_service import AutoDeleteService, _sse_event

    service = AutoDeleteService(email=payload.email, headless=payload.headless)

    try:
        yield _sse_event("status", {"step": "browser", "message": "Memulai browser..."})

        if not service.start_browser():
            yield _sse_event("error", {
                "message": f"Gagal start browser. Cookie untuk {payload.email} tidak ditemukan."
            })
            return

        yield _sse_event("status", {"step": "browser", "message": "Browser siap ✓"})
        yield _sse_event("status", {
            "step": "delete",
            "message": f"Menghapus {len(payload.comment_ids)} komentar...",
        })

        deleted = service.delete_specific_comments(
            video_id=payload.video_id,
            comment_ids=payload.comment_ids,
        )

        yield _sse_event("done", {
            "deleted": deleted,
            "requested": len(payload.comment_ids),
            "message": f"{deleted}/{len(payload.comment_ids)} komentar berhasil dihapus",
        })

    except Exception as e:
        logger.error(f"Delete stream error: {e}", exc_info=True)
        yield _sse_event("error", {"message": str(e)})
    finally:
        service.stop_browser()


def _run_fetch_comments_stream(payload: FetchCommentsRequest):
    """Generator: fetch video comments → yield SSE events."""
    from app.core.services.auto_delete_service import AutoDeleteService, _sse_event

    service = AutoDeleteService(email=payload.email, headless=payload.headless)

    try:
        yield _sse_event("status", {"step": "browser", "message": "Memulai browser..."})

        if not service.start_browser():
            yield _sse_event("error", {
                "message": f"Gagal start browser. Cookie untuk {payload.email} tidak ditemukan."
            })
            return

        yield _sse_event("status", {"step": "browser", "message": "Browser siap ✓"})
        yield _sse_event("status", {"step": "fetch", "message": "Mengambil komentar..."})

        comments = service.fetch_video_comments(video_id=payload.video_id)

        yield _sse_event("done", {
            "video_id": payload.video_id,
            "total": len(comments),
            "comments": comments,
            "message": f"{len(comments)} komentar ditemukan",
        })

    except Exception as e:
        logger.error(f"Fetch stream error: {e}", exc_info=True)
        yield _sse_event("error", {"message": str(e)})
    finally:
        service.stop_browser()


# SSE Endpoints 

@router.post("/login")
async def login_google(payload: LoginRequest):
    """
    Automatically log in to a Google account and save the YouTube Studio cookie (SSE stream).

    Email and password are auto-filled into the Google login form.
    Cookies are saved to a per-email folder and the path is stored in the database.

    SSE events:
      - `status` — progress (browser start, input_email, input_password, verify, save)
      - `done`   — {logged_in, email, channel_name, cookies_saved, cookie_count, cookie_path}
      - `error`  — error message
    """
    from app.core.services.auto_delete_service import AutoDeleteService

    logger.info("[AUTO_DELETE] Login request email=%s headless=%s", payload.email, payload.headless)
    return _sse_response(
        AutoDeleteService.login_stream(
            email=payload.email,
            password=payload.password,
            headless=payload.headless,
            timeout=payload.timeout,
        )
    )


@router.post("/scan")
async def scan_and_delete(payload: ScanRequest):
    """
    Scan a video and delete detected gambling comments (SSE stream).

    Requires `email` — the account whose stored cookie will be used.

    SSE events:
      - `status`        — progress update
      - `comment`       — safe comment
      - `judi_detected` — gambling comment detected
      - `delete`        — deletion result
      - `done`          — final summary
      - `error`         — error message
    """
    logger.info("[AUTO_DELETE] Scan+delete video_id=%s email=%s threshold=%.2f", payload.video_id, payload.email, payload.threshold)
    return _sse_response(_run_scan_stream(payload, dry_run=False))


@router.post("/scan/preview")
async def scan_preview(payload: ScanRequest):
    """
    Scan a video without deleting / dry-run (SSE stream).
    """
    logger.info("[AUTO_DELETE] Scan preview video_id=%s email=%s threshold=%.2f", payload.video_id, payload.email, payload.threshold)
    return _sse_response(_run_scan_stream(payload, dry_run=True))


@router.post("/delete")
async def delete_comments(payload: DeleteRequest):
    """
    Delete specific comments by comment ID (SSE stream).

    SSE events:
      - `status` — progress
      - `done`   — {deleted, requested, message}
      - `error`  — error message
    """
    logger.info("[AUTO_DELETE] Delete %d comments video_id=%s email=%s", len(payload.comment_ids), payload.video_id, payload.email)
    return _sse_response(_run_delete_stream(payload))


@router.post("/comments")
async def fetch_comments(payload: FetchCommentsRequest):
    """
    Fetch all comments for a video from YouTube Studio (SSE stream).
    No ML scan — returns raw comment data only.

    SSE events:
      - `status` — progress
      - `done`   — {video_id, total, comments, message}
      - `error`  — error message
    """
    logger.info("[AUTO_DELETE] Fetch comments video_id=%s email=%s", payload.video_id, payload.email)
    return _sse_response(_run_fetch_comments_stream(payload))


# JSON Endpoints (Cookie Management) 

@router.get("/cookies", response_model=APIResponse)
async def list_cookies(db: AsyncSession = Depends(get_db)):
    """
    List all stored cookie accounts (from DB + file existence check).
    Returns a regular JSON response (not SSE).
    """
    repo = CookieAccountRepository(db)
    accounts = await repo.get_all()

    from app.core.services.cookie_manager import CookieManager

    data = []
    for acc in accounts:
        mgr = CookieManager(cookie_path=acc.cookie_path)
        file_exists = mgr.exists()
        data.append({
            "id": acc.id,
            "email": acc.email,
            "channel_name": acc.channel_name,
            "cookie_path": acc.cookie_path,
            "cookie_count": acc.cookie_count,
            "is_active": bool(acc.is_active),
            "file_exists": file_exists,
            "created_at": acc.created_at.isoformat() if acc.created_at else None,
            "updated_at": acc.updated_at.isoformat() if acc.updated_at else None,
        })

    logger.info("[AUTO_DELETE] List cookies: %d accounts found", len(data))
    return success_response(
        data={"accounts": data, "total": len(data)},
        message=f"{len(data)} akun cookie ditemukan",
    )


@router.get("/cookies/{email}", response_model=APIResponse)
async def get_cookie_detail(email: str, db: AsyncSession = Depends(get_db)):
    """
    Get cookie details for a specific account.
    Returns a regular JSON response (not SSE).
    """
    repo = CookieAccountRepository(db)
    account = await repo.get_by_email(email)

    if not account:
        return error_response(message=f"Cookie untuk {email} tidak ditemukan")

    from app.core.services.cookie_manager import CookieManager

    mgr = CookieManager(cookie_path=account.cookie_path)
    file_info = mgr.get_cookie_info()

    return success_response(
        data={
            "id": account.id,
            "email": account.email,
            "channel_name": account.channel_name,
            "cookie_path": account.cookie_path,
            "cookie_count": account.cookie_count,
            "is_active": bool(account.is_active),
            "file_info": file_info,
            "created_at": account.created_at.isoformat() if account.created_at else None,
            "updated_at": account.updated_at.isoformat() if account.updated_at else None,
        },
        message=f"Cookie untuk {email}",
    )


@router.delete("/cookies/{email}", response_model=APIResponse)
async def delete_cookie_account(email: str, db: AsyncSession = Depends(get_db)):
    """
    Delete a specific cookie account (file + database record).
    Returns a regular JSON response (not SSE).
    """
    repo = CookieAccountRepository(db)
    account = await repo.get_by_email(email)

    file_deleted = False
    db_deleted = False

    if account:
        # Delete the local cookie file
        from app.core.services.cookie_manager import CookieManager
        mgr = CookieManager(cookie_path=account.cookie_path)
        file_deleted = mgr.delete()

        # Remove the database record
        db_deleted = await repo.delete_by_email(email)

    if not account:
        return error_response(message=f"Cookie untuk {email} tidak ditemukan")

    logger.info("[AUTO_DELETE] Deleted cookie email=%s file=%s db=%s", email, file_deleted, db_deleted)
    return success_response(
        data={
            "email": email,
            "file_deleted": file_deleted,
            "db_deleted": db_deleted,
        },
        message=f"Cookie untuk {email} berhasil dihapus",
    )
