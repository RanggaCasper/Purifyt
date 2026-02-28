"""YouTube Explorer endpoints.

Takes a YouTube video ID, fetches ALL comments, labels them,
and saves proportional judi/non-judi if any judi is found.
Uses Server-Sent Events (SSE) to stream progress in real time.
"""

import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.connection import get_db
from app.db.models import DataSource
from app.db.repositories.dataset_repository import DatasetRepository
from app.db.repositories.comment_repository import CommentRepository
from app.core.schemas import DatasetResponse
from app.core.services.auth_service import get_current_user

router = APIRouter(prefix="/explorer", tags=["Explorer"])


class ExploreRequest(BaseModel):
    video_id: str = Field(..., min_length=1, description="YouTube video ID")
    dataset_name: Optional[str] = Field(None, description="Nama dataset (auto-generated jika kosong)")


@router.post("/run")
async def run_explorer(
    payload: ExploreRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Explore a YouTube video by ID with real-time progress via SSE.

    Flow:
    1. Fetch ALL comments from the video
    2. Label every comment with the model (progress streamed)
    3. If 0 judi found → not saved, returns info
    4. If judi found → save proportionally (e.g. 40% judi = 40 judi + 60 normal from sample_size=100)
    5. If 100% judi → save all judi up to sample_size

    SSE event types:
      - `fetch_info`: getting video info
      - `video_info`: video title & channel
      - `fetch_comments`: fetching comments
      - `fetch_comments_done`: total comments fetched
      - `label_start`: starting labeling
      - `label_progress`: labeling progress (batch by batch)
      - `label_done`: labeling finished with counts
      - `sample`: sampling result
      - `saving`: saving to database
      - `complete`: final result with dataset & stats
      - `error`: non-fatal error
    """
    from app.core.services.explorer_service import explore_video_stream

    async def event_generator():
        final_event = None

        try:
            async for event in explore_video_stream(
                video_id=payload.video_id,
            ):
                event_type = event.get("type", "progress")

                if event_type == "done":
                    final_event = event
                    continue

                yield f"event: {event_type}\ndata: {json.dumps(event, ensure_ascii=False, default=str)}\n\n"

        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'type': 'error', 'message': f'Explorer gagal: {e}'}, ensure_ascii=False)}\n\n"
            return

        if final_event is None:
            yield f"event: error\ndata: {json.dumps({'type': 'error', 'message': 'Explorer selesai tanpa hasil'}, ensure_ascii=False)}\n\n"
            return

        comments = final_event.get("comments", [])
        stats = final_event.get("stats", {})
        message = final_event.get("message", "")

        # No judi found → don't save
        if not comments:
            done_data = {
                "type": "complete",
                "saved": False,
                "dataset": None,
                "stats": stats,
                "message": message,
            }
            yield f"event: complete\ndata: {json.dumps(done_data, ensure_ascii=False, default=str)}\n\n"
            return

        # Save to DB
        yield f"event: saving\ndata: {json.dumps({'type': 'saving', 'message': f'Menyimpan {len(comments)} komentar ke database...'}, ensure_ascii=False)}\n\n"

        try:
            video_id = stats.get("video_id", payload.video_id)
            title = stats.get("title", video_id)
            judi_pct = stats.get("judi_percentage", 0)

            name = payload.dataset_name or f"Explorer: {title} ({judi_pct}% judi)"

            ds_repo = DatasetRepository(db)
            dataset = await ds_repo.create(
                name=name,
                source=DataSource.YOUTUBE_API,
                description=(
                    f"Explorer dari video '{title}'. "
                    f"Total fetch: {stats.get('total_fetched', 0)}, "
                    f"Disimpan: {stats.get('total_saved', 0)} "
                    f"({stats.get('total_judi', 0)} judi / {stats.get('total_normal', 0)} normal)."
                ),
                source_url=f"https://www.youtube.com/watch?v={video_id}",
                owner_id=current_user.id,
            )

            rows = []
            for c in comments:
                rows.append({
                    "dataset_id": dataset.id,
                    "video_id": c["video_id"],
                    "title": c.get("title"),
                    "channel_name": c.get("channel_name"),
                    "date": c.get("date"),
                    "author": c.get("author"),
                    "comment": c.get("comment"),
                    "label": None,
                    "clean_comment": c.get("clean_comment"),
                    "predicted_label": c.get("predicted_label"),
                    "source": DataSource.YOUTUBE_API,
                    "source_detail": f"explorer:youtube:{c['video_id']}",
                })

            c_repo = CommentRepository(db)
            count = await c_repo.bulk_create(rows)

            # Explicit commit — get_db cleanup may not commit properly with SSE streaming
            await db.commit()

            dataset_info = {
                "id": dataset.id,
                "name": dataset.name,
                "description": dataset.description,
                "source": dataset.source.value,
                "source_url": dataset.source_url,
                "owner_id": dataset.owner_id,
                "created_at": dataset.created_at.isoformat(),
                "comment_count": count,
            }

        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'type': 'error', 'message': f'Gagal menyimpan ke database: {e}'}, ensure_ascii=False)}\n\n"
            return

        done_data = {
            "type": "complete",
            "saved": True,
            "dataset": dataset_info,
            "stats": stats,
            "message": (
                f"Tersimpan! {count} komentar dari '{title}'. "
                f"Judi: {stats.get('total_judi', 0)} ({judi_pct}%), "
                f"Normal: {stats.get('total_normal', 0)}."
            ),
        }
        yield f"event: complete\ndata: {json.dumps(done_data, ensure_ascii=False, default=str)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
