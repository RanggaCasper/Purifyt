import asyncio
import random
from typing import AsyncGenerator, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.modules.youtube.service import YouTubeService

logger = get_logger(__name__)

async def _predict_batch_async(texts: list[str]) -> list[dict]:
    """Run the synchronous predict_batch in a thread so it doesn't block the event loop."""
    from app.modules.labeling.service import predict_batch
    return await asyncio.to_thread(predict_batch, texts)

async def explore_channel_stream(
    channel_input: str,
    db: AsyncSession,
    max_videos: int = 10,
) -> AsyncGenerator[dict, None]:
    """
    Explore a YouTube channel:
    1. Resolve channel info (@handle or ID)
    2. Fetch recent videos from the channel
    3. For each video: fetch ALL comments, label them (streamed per batch)
    4. If video has judi -> immediately yield video_ready with sampled comments
       (ALL judi + judi x1.5 normal for that video)
    5. Yield done with aggregate stats when all videos are processed

    Event types:
      - channel_info_fetch, channel_info
      - fetch_videos, fetch_videos_done
      - video_start, video_comments, video_skip
      - label_progress: per-batch labeling progress within a video
      - label_done: per-video labeling summary
      - video_ready: video has judi -> comments ready to save (handled by endpoint)
      - video_no_judi: video has no judi, skipped
      - done: all videos processed, aggregate stats
      - error
    """
    yt = YouTubeService(db)

    yield {
        "type": "channel_info_fetch",
        "message": f"Mengambil info channel '{channel_input}'...",
    }

    try:
        channel_info = await yt.get_channel_info(channel_input)
    except Exception as e:
        yield {"type": "error", "message": f"Gagal mengambil info channel: {e}"}
        yield _done_empty(channel_input, reason=f"Channel tidak ditemukan: {e}")
        return

    channel_id = channel_info["channel_id"]
    channel_name = channel_info["title"]

    yield {
        "type": "channel_info",
        "message": f"Channel: '{channel_name}'",
        "channel_id": channel_id,
        "channel_name": channel_name,
    }

    yield {
        "type": "fetch_videos",
        "message": f"Mengambil {max_videos} video terbaru dari '{channel_name}'...",
    }

    try:
        videos = await yt.get_channel_videos(channel_id, max_results=max_videos)
    except Exception as e:
        yield {"type": "error", "message": f"Gagal mengambil video: {e}"}
        yield _done_empty(channel_input, reason=f"Gagal fetch video: {e}")
        return

    if not videos:
        yield _done_empty(channel_input, reason=f"Channel '{channel_name}' tidak memiliki video.")
        return

    yield {
        "type": "fetch_videos_done",
        "message": f"Ditemukan {len(videos)} video.",
        "total_videos": len(videos),
        "videos": [{"video_id": v["video_id"], "title": v["title"]} for v in videos],
    }

    total_comments_fetched = 0
    videos_processed = 0
    videos_with_judi = 0
    total_judi_saved = 0
    total_normal_saved = 0
    total_saved = 0

    for idx, video in enumerate(videos, 1):
        vid = video["video_id"]
        vtitle = video["title"]

        yield {
            "type": "video_start",
            "message": f"[{idx}/{len(videos)}] Memproses '{vtitle}'...",
            "video_index": idx,
            "total_videos": len(videos),
            "video_id": vid,
            "title": vtitle,
        }

        try:
            raw_comments = await yt.fetch_comments(vid, max_results=None)
        except Exception as e:
            yield {
                "type": "video_skip",
                "message": f"[{idx}/{len(videos)}] Dilewati '{vtitle}': {e}",
                "video_id": vid,
                "reason": str(e),
            }
            continue

        comment_count = len(raw_comments)
        total_comments_fetched += comment_count

        if comment_count == 0:
            yield {
                "type": "video_skip",
                "message": f"[{idx}/{len(videos)}] '{vtitle}' tidak ada komentar.",
                "video_id": vid,
                "reason": "Tidak ada komentar",
            }
            continue

        yield {
            "type": "video_comments",
            "message": f"[{idx}/{len(videos)}] '{vtitle}': {comment_count} komentar, melabeli...",
            "video_id": vid,
            "comment_count": comment_count,
        }

        # Run labeling in batches and stream progress after each batch
        texts = [c["comment"] or "" for c in raw_comments]
        predictions: list[dict] = []
        batch_size = 32
        labeled = 0

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            try:
                batch_preds = await _predict_batch_async(batch_texts)
            except Exception as e:
                logger.warning(f"Batch prediction failed for video {vid}: {e}, falling back to per-item labeling...")
                batch_preds = []
                for txt in batch_texts:
                    try:
                        single = await _predict_batch_async([txt])
                        batch_preds.extend(single)
                    except Exception:
                        batch_preds.append({"label": 0, "clean_comment": txt, "normal": 1.0, "judi": 0.0})
            predictions.extend(batch_preds)
            labeled += len(batch_preds)

            yield {
                "type": "label_progress",
                "message": f"[{idx}/{len(videos)}] '{vtitle}' - dilabeli: {labeled}/{comment_count}",
                "video_id": vid,
                "labeled": labeled,
                "total": comment_count,
                "percentage": round((labeled / comment_count) * 100, 1),
            }

        # Split results into gambling and non-gambling buckets
        judi_comments: List[dict] = []
        normal_comments: List[dict] = []

        for comment_data, pred in zip(raw_comments, predictions):
            comment_data["predicted_label"] = str(pred["label"])
            comment_data["label"] = None
            comment_data["clean_comment"] = pred["clean_comment"]

            if pred["label"] == 1:
                judi_comments.append(comment_data)
            else:
                normal_comments.append(comment_data)

        video_judi = len(judi_comments)
        video_normal = len(normal_comments)
        judi_pct = round((video_judi / comment_count) * 100, 2) if comment_count > 0 else 0

        yield {
            "type": "label_done",
            "message": (
                f"[{idx}/{len(videos)}] '{vtitle}': "
                f"{video_judi} judi ({judi_pct}%), {video_normal} non-judi"
            ),
            "video_id": vid,
            "judi_count": video_judi,
            "normal_count": video_normal,
            "judi_percentage": judi_pct,
        }

        videos_processed += 1

        if video_judi == 0:
            yield {
                "type": "video_no_judi",
                "message": f"[{idx}/{len(videos)}] '{vtitle}': tidak ada judi, dilewati.",
                "video_id": vid,
            }
            continue

        # Keep all gambling comments plus a proportional sample of normal ones (1.5x the gambling count)
        desired_normal = video_judi + round(video_judi * 0.5)
        sampled_normal_count = min(video_normal, desired_normal)
        random.shuffle(normal_comments)
        sampled = judi_comments + normal_comments[:sampled_normal_count]

        videos_with_judi += 1
        total_judi_saved += video_judi
        total_normal_saved += sampled_normal_count
        total_saved += len(sampled)

        # Hand off to the endpoint — it will save these comments to the DB right away
        # and then forward saving/video_saved SSE events back to the client.
        yield {
            "type": "video_ready",
            "message": (
                f"[{idx}/{len(videos)}] '{vtitle}': menyimpan "
                f"{video_judi} judi + {sampled_normal_count} normal = {len(sampled)} komentar"
            ),
            "video_id": vid,
            "title": vtitle,
            "channel_id": channel_id,
            "channel_name": channel_name,
            "comments": sampled,
            "video_judi": video_judi,
            "video_normal": sampled_normal_count,
            "video_total": len(sampled),
        }

    yield {
        "type": "done",
        "comments": [],  # already saved per-video by the endpoint
        "stats": _build_channel_stats(
            channel_id, channel_name, len(videos), videos_processed,
            total_comments_fetched, total_judi_saved, total_normal_saved, total_saved,
        ),
        "message": (
            f"Selesai! {videos_with_judi}/{videos_processed} video memiliki judi. "
            f"Total disimpan: {total_saved} komentar "
            f"({total_judi_saved} judi, {total_normal_saved} normal)."
        )
        if total_judi_saved > 0 else (
            f"Tidak ditemukan komentar judi di channel '{channel_name}' "
            f"({total_comments_fetched} komentar, {videos_processed} video). Tidak disimpan."
        ),
    }

def _done_empty(channel_input: str, reason: str) -> dict:
    return {
        "type": "done",
        "comments": [],
        "stats": _build_channel_stats(channel_input, "", 0, 0, 0, 0, 0, 0),
        "message": reason,
    }

def _build_channel_stats(
    channel_id: str,
    channel_name: str,
    total_videos: int,
    videos_processed: int,
    total_fetched: int,
    judi_count: int,
    normal_count: int,
    total_saved: int,
) -> dict:
    return {
        "channel_id": channel_id,
        "channel_name": channel_name,
        "total_videos": total_videos,
        "videos_processed": videos_processed,
        "total_fetched": total_fetched,
        "total_judi": judi_count,
        "total_normal": normal_count,
        "total_saved": total_saved,
        "judi_percentage": round((judi_count / total_saved) * 100, 2) if total_saved > 0 else 0,
    }
