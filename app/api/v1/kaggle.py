"""Kaggle dataset import endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.connection import get_db
from app.db.models import DataSource
from app.db.repositories.dataset_repository import DatasetRepository
from app.db.repositories.comment_repository import CommentRepository
from app.core.schemas import KaggleImportRequest, DatasetResponse
from app.core.services.kaggle_service import KaggleService
from app.core.services.auth_service import get_current_user

router = APIRouter(prefix="/kaggle", tags=["Kaggle"])


async def _do_import(
    dataset_slug: str,
    db: AsyncSession,
    owner_id: int,
    dataset_name: str = None,
) -> DatasetResponse:
    """Shared logic for Kaggle import."""
    service = KaggleService()

    try:
        result = await service.import_dataset(dataset_slug=dataset_slug)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    rows = result["rows"]
    if not rows:
        raise HTTPException(
            status_code=400,
            detail=f"No rows could be parsed. Columns found: {result['columns_found']}",
        )

    name = dataset_name or f"Kaggle: {dataset_slug}"
    ds_repo = DatasetRepository(db)
    dataset = await ds_repo.create(
        name=name,
        source=DataSource.KAGGLE,
        description=(
            f"Imported from Kaggle dataset '{dataset_slug}'. "
            f"Columns found: {result['columns_found']}"
        ),
        source_url=result["source_url"],
        owner_id=owner_id,
    )

    for row in rows:
        row["dataset_id"] = dataset.id
        row["source"] = DataSource.KAGGLE

    c_repo = CommentRepository(db)
    count = await c_repo.bulk_create(rows)

    return DatasetResponse(
        id=dataset.id,
        name=dataset.name,
        description=dataset.description,
        source=dataset.source.value,
        source_url=dataset.source_url,
        owner_id=dataset.owner_id,
        created_at=dataset.created_at,
        comment_count=count,
    )


@router.get("/import/{owner}/{dataset}", response_model=DatasetResponse)
async def import_kaggle_simple(
    owner: str,
    dataset: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Simple import: just provide the slug in the URL.

    Example: `GET /api/v1/kaggle/import/yaemico/judionline`
    """
    slug = f"{owner}/{dataset}"
    return await _do_import(
        dataset_slug=slug,
        db=db,
        owner_id=current_user.id,
    )


@router.post("/import", response_model=DatasetResponse)
async def import_kaggle_dataset(
    payload: KaggleImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Import a Kaggle dataset.

    Body only requires `dataset_slug`:
    ```json
    { "dataset_slug": "yaemico/judionline" }
    ```
    """
    return await _do_import(
        dataset_slug=payload.dataset_slug,
        db=db,
        owner_id=current_user.id,
        dataset_name=payload.dataset_name,
    )
