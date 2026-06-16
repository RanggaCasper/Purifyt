from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.logging_config import get_logger
from app.db.connection import get_db
from app.db.models import DataSource
from app.db.repositories.dataset_repository import DatasetRepository
from app.db.repositories.comment_repository import CommentRepository
from app.core.schemas import (
    YouTubeSearchRequest,
    YouTubeVideoInfo,
    DatasetResponse,
    MessageResponse,
    ScannedComment,
    YouTubeScanResponse,
)
from app.core.services.youtube_service import YouTubeService
from app.core.services.model_service import predict_batch
from app.core.services.auth_service import get_current_user
from app.utils.response_formatter import APIResponse, success_response

logger = get_logger(__name__)
router = APIRouter(prefix="/youtube", tags=["YouTube"])


@router.get("/search", response_model=APIResponse)
async def search_youtube_videos(
    query: str,
    max_results: int = 5,
    db: AsyncSession = Depends(get_db),
):
    """Search YouTube for videos matching the query. Does NOT save to DB."""
    service = YouTubeService(db)
    videos = await service.search_videos(query, max_results=max_results)
    return success_response(data=[YouTubeVideoInfo(**v) for v in videos])


@router.post("/import", response_model=APIResponse)
async def import_youtube_comments(
    payload: YouTubeSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Fetch comments from a YouTube video and save them to the database.

    - If `video_id` is provided, fetch comments directly.
    - Otherwise, search for the query and use the first result.
    """
    service = YouTubeService(db)

    video_id = payload.video_id
    if not video_id:
        # Search and pick the first video
        videos = await service.search_videos(payload.query, max_results=1)
        if not videos:
            raise HTTPException(status_code=404, detail="No videos found for query")
        video_id = videos[0]["video_id"]

    # Fetch comments (None = fetch all available)
    comment_rows = await service.fetch_comments(video_id)
    if not comment_rows:
        raise HTTPException(status_code=404, detail="No comments found for this video")

    # Create dataset
    dataset_name = payload.dataset_name or f"YouTube: {payload.query or video_id}"
    ds_repo = DatasetRepository(db)
    dataset = await ds_repo.create(
        name=dataset_name,
        source=DataSource.YOUTUBE_API,
        description=f"Comments imported from YouTube video {video_id}",
        source_url=f"https://www.youtube.com/watch?v={video_id}",
        owner_id=current_user.id,
    )

    # Bulk-insert comments
    for row in comment_rows:
        row["dataset_id"] = dataset.id
        row["source"] = DataSource.YOUTUBE_API
        row["source_detail"] = f"youtube:{video_id}"

    c_repo = CommentRepository(db)
    count = await c_repo.bulk_create(comment_rows)

    logger.info(
        "[YOUTUBE] Imported %d comments — video_id=%s dataset_id=%d",
        count, video_id, dataset.id,
    )
    return success_response(
        data=DatasetResponse(
            id=dataset.id,
            name=dataset.name,
            description=dataset.description,
            source=dataset.source.value,
            source_url=dataset.source_url,
            owner_id=dataset.owner_id,
            created_at=dataset.created_at,
            comment_count=count,
        ),
        message="YouTube comments imported successfully",
    )


@router.post("/scan", response_model=APIResponse)
async def scan_youtube_comments(
    payload: YouTubeSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Fetch YouTube comments and run spam/judi prediction WITHOUT saving to the database.

    - If `video_id` is provided, fetch comments directly.
    - Otherwise, search for the query and use the first result.
    - Returns each comment with its predicted label and confidence scores.
    """
    service = YouTubeService(db)

    video_id = payload.video_id
    if not video_id:
        videos = await service.search_videos(payload.query, max_results=1)
        if not videos:
            raise HTTPException(status_code=404, detail="No videos found for query")
        video_id = videos[0]["video_id"]

    comment_rows = await service.fetch_comments(video_id)
    if not comment_rows:
        raise HTTPException(status_code=404, detail="No comments found for this video")

    # Run batch prediction (no DB interaction)
    texts = [row.get("comment") or "" for row in comment_rows]
    predictions = predict_batch(texts)

    scanned = [
        ScannedComment(
            author=row.get("author"),
            commentId=row.get("_comment_id"),
            comment=row.get("comment"),
            clean_comment=pred["clean_comment"],
            predicted_label=pred["label"],
            confidence_normal=pred["normal"],
            confidence_judi=pred["judi"],
        )
        for row, pred in zip(comment_rows, predictions)
    ]

    judi_count = sum(1 for s in scanned if s.predicted_label == 1)
    normal_count = len(scanned) - judi_count

    logger.info(
        "[YOUTUBE] Scan complete — video_id=%s total=%d judi=%d normal=%d",
        video_id, len(scanned), judi_count, normal_count,
    )
    return success_response(
        data=YouTubeScanResponse(
            video_id=video_id,
            title=comment_rows[0].get("title"),
            channel_name=comment_rows[0].get("channel_name"),
            total_comments=len(scanned),
            judi_count=judi_count,
            normal_count=normal_count,
            comments=scanned,
        ),
        message=f"Scanned {len(scanned)} comments successfully",
    )
