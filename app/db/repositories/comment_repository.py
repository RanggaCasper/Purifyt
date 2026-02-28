from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Comment, DataSource


class CommentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, **kwargs) -> Comment:
        comment = Comment(**kwargs)
        self.db.add(comment)
        await self.db.flush()
        await self.db.refresh(comment)
        return comment

    async def bulk_create(self, comments_data: List[dict]) -> int:
        comments = [Comment(**data) for data in comments_data]
        self.db.add_all(comments)
        await self.db.flush()
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
            return None
        comment.label = label
        await self.db.flush()
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
        return count

    async def delete_by_dataset(self, dataset_id: int) -> int:
        comments = await self.get_by_dataset(dataset_id, limit=999999)
        count = len(comments)
        for c in comments:
            await self.db.delete(c)
        await self.db.flush()
        return count
