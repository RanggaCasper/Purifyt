from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.config.logging_config import get_logger
from app.db.models import Dataset, DataSource

logger = get_logger(__name__)


class DatasetRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        name: str,
        source: DataSource,
        description: str = None,
        source_url: str = None,
        owner_id: int = None,
    ) -> Dataset:
        dataset = Dataset(
            name=name,
            description=description,
            source=source,
            source_url=source_url,
            owner_id=owner_id,
        )
        self.db.add(dataset)
        await self.db.flush()
        await self.db.refresh(dataset)
        logger.info("[DATASET_REPO] Created dataset id=%d name='%s' source=%s", dataset.id, dataset.name, source.value)
        return dataset

    async def get_by_id(self, dataset_id: int) -> Optional[Dataset]:
        result = await self.db.execute(
            select(Dataset)
            .options(selectinload(Dataset.comments))
            .where(Dataset.id == dataset_id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self, skip: int = 0, limit: int = 50, source: DataSource = None
    ) -> List[Dataset]:
        query = select(Dataset)
        if source:
            query = query.where(Dataset.source == source)
        query = query.order_by(Dataset.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def count(self, source: DataSource = None) -> int:
        query = select(func.count(Dataset.id))
        if source:
            query = query.where(Dataset.source == source)
        result = await self.db.execute(query)
        return result.scalar()

    async def delete(self, dataset_id: int) -> bool:
        dataset = await self.get_by_id(dataset_id)
        if dataset:
            await self.db.delete(dataset)
            await self.db.flush()
            logger.info("[DATASET_REPO] Deleted dataset id=%d", dataset_id)
            return True
        logger.warning("[DATASET_REPO] Delete failed: dataset_id=%d not found", dataset_id)
        return False
