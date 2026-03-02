from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.logging_config import get_logger
from app.db.models import Comment, DataSource
from app.utils.text_cleaner import clean_comment as _clean_comment

logger = get_logger(__name__)


def _apply_clean_comment(data: dict) -> dict:
    """Ensure clean_comment is always derived from comment via clean_comment()."""
    raw = data.get("comment")
    if raw:
        data["clean_comment"] = _clean_comment(raw)
    return data


class CommentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, **kwargs) -> Comment:
        kwargs = _apply_clean_comment(kwargs)
        comment = Comment(**kwargs)
        self.db.add(comment)
        await self.db.flush()
        await self.db.refresh(comment)
        return comment

    async def bulk_create(self, comments_data: List[dict]) -> int:
        comments = [Comment(**_apply_clean_comment(data)) for data in comments_data]
        self.db.add_all(comments)
        await self.db.flush()
        logger.debug("[COMMENT_REPO] bulk_create inserted %d comments", len(comments))
        return len(comments)

    async def get_by_id(self, comment_id: int) -> Optional[Comment]:
        result = await self.db.execute(select(Comment).where(Comment.id == comment_id))
        return result.scalar_one_or_none()

    async def get_by_dataset(
        self, dataset_id: int, skip: int = 0, limit: int = 100
    ) -> List[Comment]:
        result = await self.db.execute(
            select(Comment)
            .where(Comment.dataset_id == dataset_id)
            .order_by(Comment.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_video_id(
        self, video_id: str, skip: int = 0, limit: int = 100
    ) -> List[Comment]:
        result = await self.db.execute(
            select(Comment)
            .where(Comment.video_id == video_id)
            .order_by(Comment.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def search(
        self, keyword: str, skip: int = 0, limit: int = 100
    ) -> List[Comment]:
        result = await self.db.execute(
            select(Comment)
            .where(Comment.comment.contains(keyword))
            .order_by(Comment.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def count_by_dataset(self, dataset_id: int) -> int:
        result = await self.db.execute(
            select(func.count(Comment.id)).where(Comment.dataset_id == dataset_id)
        )
        return result.scalar()

    async def count_search(self, keyword: str) -> int:
        result = await self.db.execute(
            select(func.count(Comment.id)).where(Comment.comment.contains(keyword))
        )
        return result.scalar()

    async def update_label(self, comment_id: int, label: Optional[str]) -> Optional[Comment]:
        comment = await self.get_by_id(comment_id)
        if not comment:
            logger.warning("[COMMENT_REPO] update_label: comment_id=%d not found", comment_id)
            return None
        comment.label = label
        await self.db.flush()
        logger.debug("[COMMENT_REPO] update_label comment_id=%d label=%s", comment_id, label)
        return comment

    async def bulk_update_labels(self, updates: List[dict]) -> int:
        """updates: list of {comment_id, label}"""
        count = 0
        for item in updates:
            comment = await self.get_by_id(item["comment_id"])
            if comment:
                comment.label = item["label"]
                count += 1
        await self.db.flush()
        logger.info("[COMMENT_REPO] bulk_update_labels updated=%d/%d", count, len(updates))
        return count

    async def delete_by_dataset(self, dataset_id: int) -> int:
        comments = await self.get_by_dataset(dataset_id, limit=999999)
        count = len(comments)
        for c in comments:
            await self.db.delete(c)
        await self.db.flush()
        logger.info("[COMMENT_REPO] delete_by_dataset dataset_id=%d deleted=%d", dataset_id, count)
        return count

    async def reprocess_clean_comments(self, batch_size: int = 500) -> int:
        """Re-apply clean_comment() to all existing rows in batches.
        Returns total number of rows updated."""
        offset = 0
        total_updated = 0
        while True:
            result = await self.db.execute(
                select(Comment)
                .where(Comment.comment.isnot(None))
                .order_by(Comment.id)
                .offset(offset)
                .limit(batch_size)
            )
            batch = result.scalars().all()
            if not batch:
                break
            for row in batch:
                row.clean_comment = _clean_comment(row.comment)
            await self.db.flush()
            total_updated += len(batch)
            offset += batch_size
        logger.info("[COMMENT_REPO] reprocess_clean_comments updated=%d rows", total_updated)
        return total_updated
