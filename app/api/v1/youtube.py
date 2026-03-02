from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.connection import get_db
from app.db.models import DataSource
from app.db.repositories.dataset_repository import DatasetRepository
from app.db.repositories.comment_repository import CommentRepository
from app.core.schemas import (
    YouTubeSearchRequest,
    YouTubeVideoInfo,
    DatasetResponse,
    MessageResponse,
)
from app.core.services.youtube_service import YouTubeService
from app.core.services.auth_service import get_current_user
from app.utils.response_formatter import APIResponse, success_response

router = APIRouter(prefix="/youtube", tags=["YouTube"])


@router.get("/search", response_model=APIResponse)
async def search_youtube_videos(
    query: str,
    max_results: int = 5,
):
    """Search YouTube for videos matching the query. Does NOT save to DB."""
    service = YouTubeService()
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
    service = YouTubeService()

    video_id = payload.video_id
    if not video_id:
        # Search and pick the first video
        videos = await service.search_videos(payload.query, max_results=1)
        if not videos:
            raise HTTPException(status_code=404, detail="No videos found for query")
        video_id = videos[0]["video_id"]

    # Fetch comments (None = fetch all available)
    comment_rows = await service.fetch_comments(video_id, max_results=payload.max_results)
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
