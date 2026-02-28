"""YouTube Channel Explorer service.

Takes a YouTube channel ID or @handle, fetches recent videos,
then explores each video's comments — labels them and collects
judi/non-judi results across the entire channel.

Uses async generator to stream progress events in real time.
"""

import asyncio
import random
import logging
from typing import AsyncGenerator, List, Optional

from app.core.services.youtube_service import YouTubeService

logger = logging.getLogger(__name__)


async def _predict_batch_async(texts: list[str]) -> list[dict]:
    """Run the synchronous predict_batch in a thread so it doesn't block the event loop."""
    from app.core.services.model_service import predict_batch
    return await asyncio.to_thread(predict_batch, texts)


async def explore_channel_stream(
    channel_input: str,
    max_videos: int = 10,
) -> AsyncGenerator[dict, None]:
    """
    Explore a YouTube channel:
    1. Resolve channel info (@handle or ID)
    2. Fetch recent videos from the channel
    3. For each video: fetch ALL comments, label them
    4. Aggregate all judi + sample normal across all videos
    5. Save ALL judi + (judi + 10) normal

    Yields progress events for SSE streaming.
    Final event type is "done" with all comments and stats.
    """
    yt = YouTubeService()

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

    all_judi: List[dict] = []
    all_normal: List[dict] = []
    total_comments_fetched = 0
    videos_processed = 0
    videos_with_judi = 0

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

        # Fetch comments for this video
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

        # Label comments
        texts = [c["comment"] or "" for c in raw_comments]
        predictions: list[dict] = []
        batch_size = 32

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            try:
                batch_preds = await _predict_batch_async(batch_texts)
            except Exception as e:
                logger.warning(f"Batch failed for video {vid}: {e}, labeling individually...")
                batch_preds = []
                for txt in batch_texts:
                    try:
                        single = await _predict_batch_async([txt])
                        batch_preds.extend(single)
                    except Exception:
                        batch_preds.append({"label": 0, "clean_comment": txt, "normal": 1.0, "judi": 0.0})
            predictions.extend(batch_preds)

        # Separate judi vs normal
        video_judi = 0
        video_normal = 0
        for comment_data, pred in zip(raw_comments, predictions):
            comment_data["predicted_label"] = str(pred["label"])
            comment_data["label"] = None
            comment_data["clean_comment"] = pred["clean_comment"]

            if pred["label"] == 1:
                all_judi.append(comment_data)
                video_judi += 1
            else:
                all_normal.append(comment_data)
                video_normal += 1

        videos_processed += 1
        if video_judi > 0:
            videos_with_judi += 1

        yield {
            "type": "video_done",
            "message": (
                f"[{idx}/{len(videos)}] '{vtitle}': "
                f"{video_judi} judi, {video_normal} non-judi"
            ),
            "video_id": vid,
            "title": vtitle,
            "judi_count": video_judi,
            "normal_count": video_normal,
        }

    total_judi = len(all_judi)
    total_normal_available = len(all_normal)
    judi_pct = round((total_judi / total_comments_fetched) * 100, 2) if total_comments_fetched > 0 else 0

    yield {
        "type": "label_done",
        "message": (
            f"Total: {total_judi} judi ({judi_pct}%), "
            f"{total_normal_available} non-judi dari {total_comments_fetched} komentar "
            f"({videos_processed} video, {videos_with_judi} memiliki judi)"
        ),
        "total_fetched": total_comments_fetched,
        "judi_count": total_judi,
        "normal_count": total_normal_available,
        "judi_percentage": judi_pct,
        "videos_processed": videos_processed,
        "videos_with_judi": videos_with_judi,
    }

    if total_judi == 0:
        yield {
            "type": "done",
            "comments": [],
            "stats": _build_channel_stats(
                channel_id, channel_name, len(videos), videos_processed,
                total_comments_fetched, 0, 0, 0,
            ),
            "message": (
                f"Tidak ditemukan komentar judi di channel '{channel_name}' "
                f"({total_comments_fetched} komentar, {videos_processed} video). Tidak disimpan."
            ),
        }
        return

    sampled_judi = total_judi
    desired_normal = total_judi + 10
    sampled_normal = min(total_normal_available, desired_normal)

    random.shuffle(all_normal)
    sampled = all_judi + all_normal[:sampled_normal]

    total_sampled = len(sampled)
    sampled_judi_pct = round((sampled_judi / total_sampled) * 100, 2) if total_sampled > 0 else 0

    yield {
        "type": "sample",
        "message": (
            f"Sample: {sampled_judi} judi + {sampled_normal} non-judi = "
            f"{total_sampled} komentar ({sampled_judi_pct}% judi)"
        ),
        "sampled_judi": sampled_judi,
        "sampled_normal": sampled_normal,
        "total_sampled": total_sampled,
    }

    yield {
        "type": "done",
        "comments": sampled,
        "stats": _build_channel_stats(
            channel_id, channel_name, len(videos), videos_processed,
            total_comments_fetched, sampled_judi, sampled_normal, total_sampled,
        ),
        "message": (
            f"Ditemukan {total_judi} judi dari {total_comments_fetched} komentar "
            f"({videos_processed} video). "
            f"Menyimpan {total_sampled} komentar ({sampled_judi} judi, {sampled_normal} normal)."
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
