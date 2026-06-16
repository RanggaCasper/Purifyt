import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.logging_config import get_logger
from app.db.connection import get_db
from app.db.models import DataSource
from app.db.repositories.dataset_repository import DatasetRepository
from app.db.repositories.comment_repository import CommentRepository
from app.core.services.auth_service import get_current_user

logger = get_logger(__name__)
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
    3. For each video: fetch ALL comments, label per batch (streamed)
    4. If video has judi → save immediately to DB (ALL judi + judi×1.5 normal)
    5. Stream complete event with aggregate stats when all videos done

    SSE event types:
      - `channel_info_fetch`: resolving channel
      - `channel_info`: channel name & ID
      - `fetch_videos`: fetching video list
      - `fetch_videos_done`: video list result
      - `video_start`: starting a video
      - `video_comments`: comments fetched for a video
      - `video_skip`: video skipped (error/no comments)
      - `label_progress`: per-batch labeling progress for current video
      - `label_done`: per-video labeling summary
      - `video_no_judi`: video has no judi, skipped
      - `saving`: saving video comments to database
      - `video_saved`: video comments saved successfully
      - `complete`: all videos done with aggregate stats
      - `error`: error event
    """
    from app.core.services.channel_explorer_service import explore_channel_stream

    logger.info("[CHANNEL_EXPLORER] Starting channel=%s max_videos=%d user_id=%d", payload.channel, payload.max_videos, current_user.id)

    async def event_generator():
        dataset = None
        dataset_info = None
        total_count = 0
        final_event = None

        try:
            try:
                stream = explore_channel_stream(
                    channel_input=payload.channel,
                    db=db,
                    max_videos=payload.max_videos,
                )
            except TypeError:
                stream = explore_channel_stream(
                    channel_input=payload.channel,
                    max_videos=payload.max_videos,
                )

            async for event in stream:
                event_type = event.get("type", "progress")

                # Intercept video_ready → save to DB immediately (only if dataset_name provided)
                if event_type == "video_ready":
                    comments = event.get("comments", [])
                    vid = event.get("video_id", "")
                    vtitle = event.get("title", vid)
                    channel_id = event.get("channel_id", "")
                    channel_name = event.get("channel_name", payload.channel)
                    video_judi = event.get("video_judi", 0)
                    video_normal = event.get("video_normal", 0)

                    # Scan-only mode: skip DB jika dataset_name tidak diisi
                    if not payload.dataset_name:
                        yield f"event: video_saved\ndata: {json.dumps({'type': 'video_saved', 'message': f'[Scan only] {len(comments)} komentar dari \"{vtitle}\" ({video_judi} judi, {video_normal} normal) — tidak disimpan', 'video_id': vid, 'count': 0, 'judi': video_judi, 'normal': video_normal, 'dataset_id': None}, ensure_ascii=False)}\n\n"
                        continue

                    yield f"event: saving\ndata: {json.dumps({'type': 'saving', 'message': f'Menyimpan {len(comments)} komentar dari \"{vtitle}\"...', 'video_id': vid}, ensure_ascii=False)}\n\n"

                    try:
                        # Create dataset lazily on first video with judi
                        if dataset is None:
                            name = payload.dataset_name
                            ds_repo = DatasetRepository(db)
                            dataset = await ds_repo.create(
                                name=name,
                                source=DataSource.YOUTUBE_API,
                                description=f"Channel explorer '{channel_name}' — {payload.channel}",
                                source_url=f"https://www.youtube.com/channel/{channel_id}",
                                owner_id=current_user.id,
                            )
                            dataset_info = {
                                "id": dataset.id,
                                "name": dataset.name,
                                "source": dataset.source.value,
                                "source_url": dataset.source_url,
                                "owner_id": dataset.owner_id,
                                "created_at": dataset.created_at.isoformat(),
                            }

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
                        await db.commit()
                        total_count += count

                        yield f"event: video_saved\ndata: {json.dumps({'type': 'video_saved', 'message': f'Tersimpan {count} komentar dari \"{vtitle}\" ({video_judi} judi, {video_normal} normal)', 'video_id': vid, 'count': count, 'judi': video_judi, 'normal': video_normal, 'dataset_id': dataset.id}, ensure_ascii=False)}\n\n"

                    except Exception as e:
                        yield f"event: error\ndata: {json.dumps({'type': 'error', 'message': f'Gagal menyimpan video \"{vtitle}\": {e}'}, ensure_ascii=False)}\n\n"

                    continue

                # Capture final done event
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

        stats = final_event.get("stats", {})
        message = final_event.get("message", "")

        if dataset_info:
            dataset_info["comment_count"] = total_count

        done_data = {
            "type": "complete",
            "saved": dataset is not None,
            "dataset": dataset_info,
            "stats": stats,
            "message": message,
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

