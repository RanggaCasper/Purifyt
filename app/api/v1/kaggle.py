from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.connection import get_db
from app.db.models import DataSource
from app.modules.datasets.repository import DatasetRepository
from app.modules.datasets.comment_repository import CommentRepository
from app.modules.datasets.schemas import DatasetResponse
from app.modules.kaggle.schemas import KaggleImportRequest
from app.modules.kaggle.service import KaggleService
from app.modules.auth.service import get_current_user
from app.shared.utils.response_formatter import APIResponse, success_response

logger = get_logger(__name__)
router = APIRouter(prefix="/kaggle", tags=["Kaggle"])


async def _do_import(
    dataset_slug: str,
    db: AsyncSession,
    owner_id: int,
    dataset_name: str = None,
    column_mapping: dict[str, str] | None = None,
) -> DatasetResponse:
    """Shared logic for Kaggle import."""
    logger.info("[KAGGLE] Starting import — slug='%s' owner_id=%d", dataset_slug, owner_id)
    service = KaggleService(db)

    try:
        result = await service.import_dataset(
            dataset_slug=dataset_slug,
            column_mapping=column_mapping,
        )
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
            f"Columns found: {result['columns_found']}. "
            f"Column mapping: {result.get('column_mapping', {})}"
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


@router.get("/import/{owner}/{dataset}", response_model=APIResponse)
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
    return success_response(
        data=await _do_import(dataset_slug=slug, db=db, owner_id=current_user.id),
        message="Kaggle dataset imported successfully",
    )


@router.post("/import", response_model=APIResponse)
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

    Optional manual column mapping uses database field -> Kaggle column:
    ```json
    { "dataset_slug": "user/data", "column_mapping": { "comment": "text", "author": "username" } }
    ```
    """
    return success_response(
        data=await _do_import(
            dataset_slug=payload.dataset_slug,
            db=db,
            owner_id=current_user.id,
            dataset_name=payload.dataset_name,
            column_mapping=payload.column_mapping,
        ),
        message="Kaggle dataset imported successfully",
    )
