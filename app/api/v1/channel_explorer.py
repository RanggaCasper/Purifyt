"""YouTube Channel Explorer endpoints.

Takes a YouTube channel (@handle or ID), fetches recent videos,
explores comments from each video, labels them, and saves results.
Uses Server-Sent Events (SSE) to stream progress in real time.
"""

import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.connection import get_db
from app.db.models import DataSource
from app.db.repositories.dataset_repository import DatasetRepository
from app.db.repositories.comment_repository import CommentRepository
from app.core.services.auth_service import get_current_user

router = APIRouter(prefix="/explorer/channel", tags=["Explorer"])


class ChannelExploreRequest(BaseModel):
    channel: str = Field(
        ...,
        min_length=1,
        description="YouTube channel @handle (e.g. '@MILYHYA') atau channel ID (e.g. 'UCxxxxxxxx')",
    )
    max_videos: int = Field(
        10, ge=1, le=50,
        description="Jumlah video terbaru yang akan diproses",
    )
    dataset_name: Optional[str] = Field(
        None,
        description="Nama dataset (auto-generated jika kosong)",
    )


@router.post("/run")
async def run_channel_explorer(
    payload: ChannelExploreRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Explore a YouTube channel with real-time progress via SSE.

    Flow:
    1. Resolve channel info from @handle or channel ID
    2. Fetch recent videos (up to max_videos)
    3. For each video: fetch ALL comments, label them
    4. Aggregate results across all videos
    5. Save ALL judi + (judi + 10) normal comments

    SSE event types:
      - `channel_info_fetch`: resolving channel
      - `channel_info`: channel name & ID
      - `fetch_videos`: fetching video list
      - `fetch_videos_done`: video list result
      - `video_start`: starting a video
      - `video_comments`: comments fetched for a video
      - `video_done`: video processing result
      - `video_skip`: video skipped (error/no comments)
      - `label_done`: overall labeling summary
      - `sample`: sampling result
      - `saving`: saving to database
      - `complete`: final result with dataset & stats
      - `error`: error event
    """
    from app.core.services.channel_explorer_service import explore_channel_stream

    async def event_generator():
        final_event = None

        try:
            async for event in explore_channel_stream(
                channel_input=payload.channel,
                max_videos=payload.max_videos,
            ):
                event_type = event.get("type", "progress")

                if event_type == "done":
                    final_event = event
                    continue

                yield f"event: {event_type}\ndata: {json.dumps(event, ensure_ascii=False, default=str)}\n\n"

        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'type': 'error', 'message': f'Channel explorer gagal: {e}'}, ensure_ascii=False)}\n\n"
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
            channel_name = stats.get("channel_name", payload.channel)
            channel_id = stats.get("channel_id", "")
            judi_pct = stats.get("judi_percentage", 0)

            name = payload.dataset_name or (
                f"Channel: {channel_name} ({stats.get('total_judi', 0)} judi, "
                f"{stats.get('videos_processed', 0)} video)"
            )

            ds_repo = DatasetRepository(db)
            dataset = await ds_repo.create(
                name=name,
                source=DataSource.YOUTUBE_API,
                description=(
                    f"Channel explorer '{channel_name}'. "
                    f"Video diproses: {stats.get('videos_processed', 0)}/{stats.get('total_videos', 0)}, "
                    f"Total komentar: {stats.get('total_fetched', 0)}, "
                    f"Disimpan: {stats.get('total_saved', 0)} "
                    f"({stats.get('total_judi', 0)} judi / {stats.get('total_normal', 0)} normal)."
                ),
                source_url=f"https://www.youtube.com/channel/{channel_id}",
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
                    "source_detail": f"explorer:channel:{channel_id}:{c['video_id']}",
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
                f"Tersimpan! {count} komentar dari channel '{channel_name}'. "
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
