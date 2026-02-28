from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.connection import get_db
from app.db.models import DataSource
from app.db.repositories.dataset_repository import DatasetRepository
from app.db.repositories.comment_repository import CommentRepository
from app.core.schemas import (
    DatasetCreate,
    DatasetResponse,
    DatasetDetailResponse,
    CommentResponse,
    MessageResponse,
)
from app.core.services.auth_service import get_current_user
from app.utils.response_formatter import APIResponse, success_response

router = APIRouter(prefix="/datasets", tags=["Datasets"])


@router.get("/", response_model=APIResponse)
async def list_datasets(
    skip: int = 0,
    limit: int = 50,
    source: str = Query(None, description="Filter by source: youtube_api, kaggle, manual"),
    db: AsyncSession = Depends(get_db),
):
    repo = DatasetRepository(db)
    comment_repo = CommentRepository(db)
    ds_source = DataSource(source) if source else None
    datasets = await repo.get_all(skip=skip, limit=limit, source=ds_source)
    results = []
    for ds in datasets:
        count = await comment_repo.count_by_dataset(ds.id)
        results.append(
            DatasetResponse(
                id=ds.id,
                name=ds.name,
                description=ds.description,
                source=ds.source.value,
                source_url=ds.source_url,
                owner_id=ds.owner_id,
                created_at=ds.created_at,
                comment_count=count,
            )
        )
    return success_response(data=results)


@router.get("/{dataset_id}", response_model=APIResponse)
async def get_dataset(
    dataset_id: int,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    repo = DatasetRepository(db)
    ds = await repo.get_by_id(dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    comment_repo = CommentRepository(db)
    comments = await comment_repo.get_by_dataset(dataset_id, skip=skip, limit=limit)
    return success_response(data=DatasetDetailResponse(
        id=ds.id,
        name=ds.name,
        description=ds.description,
        source=ds.source.value,
        source_url=ds.source_url,
        owner_id=ds.owner_id,
        created_at=ds.created_at,
        comment_count=await comment_repo.count_by_dataset(ds.id),
        comments=[
            CommentResponse(
                id=c.id,
                dataset_id=c.dataset_id,
                video_id=c.video_id,
                title=c.title,
                channel_name=c.channel_name,
                date=c.date,
                author=c.author,
                comment=c.comment,
                label=c.label,
                clean_comment=c.clean_comment,
                predicted_label=c.predicted_label,
                source=c.source.value,
                source_detail=c.source_detail,
                created_at=c.created_at,
            )
            for c in comments
        ],
    ))


@router.delete("/{dataset_id}", response_model=APIResponse)
async def delete_dataset(
    dataset_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    repo = DatasetRepository(db)
    deleted = await repo.delete(dataset_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return success_response(message="Dataset deleted successfully")


@router.get("/{dataset_id}/comments", response_model=APIResponse)
async def list_comments(
    dataset_id: int,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    comment_repo = CommentRepository(db)
    comments = await comment_repo.get_by_dataset(dataset_id, skip=skip, limit=limit)
    return success_response(data=[
        CommentResponse(
            id=c.id,
            dataset_id=c.dataset_id,
            video_id=c.video_id,
            title=c.title,
            channel_name=c.channel_name,
            date=c.date,
            author=c.author,
            comment=c.comment,
            label=c.label,
            clean_comment=c.clean_comment,
            predicted_label=c.predicted_label,
            source=c.source.value,
            source_detail=c.source_detail,
            created_at=c.created_at,
        )
        for c in comments
    ])


@router.get("/search/comments", response_model=APIResponse)
async def search_comments(
    keyword: str = Query(..., min_length=1),
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    comment_repo = CommentRepository(db)
    comments = await comment_repo.search(keyword, skip=skip, limit=limit)
    return success_response(data=[
        CommentResponse(
            id=c.id,
            dataset_id=c.dataset_id,
            video_id=c.video_id,
            title=c.title,
            channel_name=c.channel_name,
            date=c.date,
            author=c.author,
            comment=c.comment,
            label=c.label,
            clean_comment=c.clean_comment,
            predicted_label=c.predicted_label,
            source=c.source.value,
            source_detail=c.source_detail,
            created_at=c.created_at,
        )
        for c in comments
    ])
