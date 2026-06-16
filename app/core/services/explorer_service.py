import asyncio
import random
from typing import AsyncGenerator, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.logging_config import get_logger
from app.core.services.youtube_service import YouTubeService

logger = get_logger(__name__)

async def _predict_batch_async(texts: list[str]) -> list[dict]:
    """Run the synchronous predict_batch in a thread so it doesn't block the event loop."""
    from app.core.services.model_service import predict_batch
    return await asyncio.to_thread(predict_batch, texts)

async def explore_video_stream(
    video_id: str,
    db: AsyncSession,
) -> AsyncGenerator[dict, None]:
    """
    Explore a single YouTube video:
    1. Fetch ALL comments
    2. Label every comment with the model
    3. If 0 judi → yield done with no comments (don't save)
    4. If judi found → save ALL judi + (judi × 1.5) normal
       e.g. 86 judi → 86 judi + 129 normal = 215

    Yields progress events with {"type": "...", ...}
    Final event type is "done" with comments list and stats.
    """
    yt = YouTubeService(db)

    yield {
        "type": "fetch_info",
        "message": f"Mengambil info video {video_id}...",
        "video_id": video_id,
    }

    try:
        video_info = await yt._get_video_info(video_id)
    except Exception as e:
        yield {"type": "error", "message": f"Gagal mengambil info video: {e}"}
        yield _done_empty(video_id, reason=f"Video tidak ditemukan: {e}")
        return

    title = video_info.get("title", video_id)
    channel = video_info.get("channel_name", "")

    yield {
        "type": "video_info",
        "message": f"Video: '{title}' oleh {channel}",
        "video_id": video_id,
        "title": title,
        "channel_name": channel,
    }

    yield {
        "type": "fetch_comments",
        "message": f"Mengambil semua komentar dari '{title}'...",
        "video_id": video_id,
    }

    try:
        raw_comments = await yt.fetch_comments(video_id, max_results=None)
    except Exception as e:
        yield {"type": "error", "message": f"Gagal mengambil komentar: {e}"}
        yield _done_empty(video_id, reason=f"Gagal fetch komentar: {e}")
        return

    total_fetched = len(raw_comments)
    if total_fetched == 0:
        yield {
            "type": "fetch_comments_done",
            "message": "Tidak ada komentar ditemukan.",
            "total_fetched": 0,
        }
        yield _done_empty(video_id, reason="Video tidak memiliki komentar.")
        return

    yield {
        "type": "fetch_comments_done",
        "message": f"Berhasil mengambil {total_fetched} komentar.",
        "total_fetched": total_fetched,
    }

    yield {
        "type": "label_start",
        "message": f"Melabeli {total_fetched} komentar...",
        "total": total_fetched,
    }

    texts = [c["comment"] or "" for c in raw_comments]
    all_predictions: list[dict] = []
    batch_size = 32
    labeled = 0

    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        try:
            batch_preds = await _predict_batch_async(batch_texts)
        except Exception as e:
            logger.warning(f"Batch {i // batch_size + 1} failed: {e}, labeling individually...")
            # Fallback: label one-by-one so one bad comment doesn't kill the batch
            batch_preds = []
            for txt in batch_texts:
                try:
                    single = await _predict_batch_async([txt])
                    batch_preds.extend(single)
                except Exception:
                    # Skip this comment entirely — mark as normal
                    batch_preds.append({"label": 0, "clean_comment": txt, "normal": 1.0, "judi": 0.0})

        all_predictions.extend(batch_preds)
        labeled += len(batch_preds)

        yield {
            "type": "label_progress",
            "message": f"Dilabeli: {labeled}/{total_fetched}",
            "labeled": labeled,
            "total": total_fetched,
            "percentage": round((labeled / total_fetched) * 100, 1),
        }

    judi_comments = []
    normal_comments = []

    for comment_data, pred in zip(raw_comments, all_predictions):
        comment_data["predicted_label"] = str(pred["label"])
        comment_data["label"] = None
        comment_data["clean_comment"] = pred["clean_comment"]

        if pred["label"] == 1:
            judi_comments.append(comment_data)
        else:
            normal_comments.append(comment_data)

    judi_count = len(judi_comments)
    normal_count = len(normal_comments)
    judi_pct = round((judi_count / total_fetched) * 100, 2) if total_fetched > 0 else 0

    yield {
        "type": "label_done",
        "message": (
            f"Selesai labeling: {judi_count} judi ({judi_pct}%), "
            f"{normal_count} non-judi dari {total_fetched} total"
        ),
        "judi_count": judi_count,
        "normal_count": normal_count,
        "judi_percentage": judi_pct,
    }

    if judi_count == 0:
        yield {
            "type": "done",
            "comments": [],
            "stats": _build_stats(video_id, title, channel, total_fetched, 0, 0, 0),
            "message": (
                f"Tidak ditemukan komentar judi di '{title}' "
                f"({total_fetched} komentar). Tidak disimpan."
            ),
        }
        return

    sampled_judi = judi_count
    desired_normal = judi_count + round(judi_count * 0.5)
    sampled_normal = min(normal_count, desired_normal)

    random.shuffle(normal_comments)
    sampled = judi_comments + normal_comments[:sampled_normal]

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
        "stats": _build_stats(
            video_id, title, channel,
            total_fetched, sampled_judi, total_sampled - sampled_judi, total_sampled,
        ),
        "message": (
            f"Ditemukan {judi_count} judi dari {total_fetched} komentar. "
            f"Menyimpan {total_sampled} komentar ({sampled_judi} judi, {total_sampled - sampled_judi} normal)."
        ),
    }

def _done_empty(video_id: str, reason: str) -> dict:
    """Helper to yield a done event with no comments."""
    return {
        "type": "done",
        "comments": [],
        "stats": _build_stats(video_id, "", "", 0, 0, 0, 0),
        "message": reason,
    }

def _build_stats(
    video_id: str,
    title: str,
    channel_name: str,
    total_fetched: int,
    judi_count: int,
    normal_count: int,
    total_saved: int,
) -> dict:
    return {
        "video_id": video_id,
        "title": title,
        "channel_name": channel_name,
        "total_fetched": total_fetched,
        "total_judi": judi_count,
        "total_normal": normal_count,
        "total_saved": total_saved,
        "judi_percentage": round((judi_count / total_saved) * 100, 2) if total_saved > 0 else 0,
    }
