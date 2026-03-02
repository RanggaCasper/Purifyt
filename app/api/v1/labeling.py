from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.connection import get_db
from app.db.models import Comment
from app.db.repositories.comment_repository import CommentRepository
from app.core.schemas import CommentResponse
from app.core.services.auth_service import get_current_user
from app.utils.response_formatter import APIResponse, success_response

router = APIRouter(prefix="/labeling", tags=["Labeling"])


class PredictRequest(BaseModel):
    text: str = Field(..., min_length=1)


class PredictResponse(BaseModel):
    text: str
    clean_comment: str
    label: int  # 0 = non judi, 1 = judi online
    normal: float
    judi: float


class BatchPredictRequest(BaseModel):
    texts: list[str] = Field(..., min_length=1)


class LabelDatasetResponse(BaseModel):
    dataset_id: int
    total_comments: int
    labeled_count: int
    normal_count: int
    judi_count: int
    judi_percentage: float


class ManualLabelRequest(BaseModel):
    label: Literal["0", "1"] = Field(
        ..., description="0 = non judi (koreksi false positive), 1 = judi online (koreksi false negative)"
    )


class BulkManualLabelItem(BaseModel):
    comment_id: int
    label: Literal["0", "1"]


class BulkManualLabelRequest(BaseModel):
    labels: List[BulkManualLabelItem] = Field(..., min_length=1)


class BulkManualLabelResponse(BaseModel):
    updated_count: int
    skipped_count: int


@router.post("/predict", response_model=APIResponse)
async def predict_single(payload: PredictRequest):
    """Predict a single comment text."""
    from app.core.services.model_service import predict
    try:
        result = predict(payload.text)
    except (RuntimeError, FileNotFoundError) as e:
        raise HTTPException(status_code=500, detail=str(e))
    return success_response(data=PredictResponse(text=payload.text, **result))


@router.post("/predict/batch", response_model=APIResponse)
async def predict_batch(payload: BatchPredictRequest):
    """Predict a batch of comment texts."""
    from app.core.services.model_service import predict_batch as pb
    try:
        results = pb(payload.texts)
    except (RuntimeError, FileNotFoundError) as e:
        raise HTTPException(status_code=500, detail=str(e))
    return success_response(data=[PredictResponse(text=t, **r) for t, r in zip(payload.texts, results)])


@router.post("/dataset/{dataset_id}", response_model=APIResponse)
async def label_dataset(
    dataset_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """
    Auto-label all comments in a dataset using the model.
    Cleans each comment (remove emoji, lowercase), stores clean_comment,
    and sets predicted_label to 0 (non judi) or 1 (judi online).
    """
    from app.core.services.model_service import predict_batch as pb

    result = await db.execute(
        select(Comment).where(Comment.dataset_id == dataset_id)
    )
    comments = result.scalars().all()

    if not comments:
        raise HTTPException(status_code=404, detail="No comments found in this dataset")

    texts = [c.comment or "" for c in comments]

    try:
        predictions = pb(texts)
    except (RuntimeError, FileNotFoundError) as e:
        raise HTTPException(status_code=500, detail=str(e))

    normal_count = 0
    judi_count = 0
    for comment, pred in zip(comments, predictions):
        comment.clean_comment = pred["clean_comment"]
        comment.predicted_label = str(pred["label"])  # "0" or "1"
        if pred["label"] == 1:
            judi_count += 1
        else:
            normal_count += 1

    await db.flush()

    total = len(comments)
    return success_response(
        data=LabelDatasetResponse(
            dataset_id=dataset_id,
            total_comments=total,
            labeled_count=total,
            normal_count=normal_count,
            judi_count=judi_count,
            judi_percentage=round((judi_count / total) * 100, 2) if total > 0 else 0,
        ),
        message=f"{total} comments labeled successfully",
    )


@router.patch("/comment/{comment_id}", response_model=APIResponse)
async def manual_label_comment(
    comment_id: int,
    payload: ManualLabelRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """
    Koreksi label manual pada satu comment.
    Gunakan ini jika model salah prediksi (false positive/false negative).
    Field `label` yang diupdate, bukan `predicted_label`.
    """
    repo = CommentRepository(db)
    comment = await repo.update_label(comment_id, payload.label)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    await db.commit()
    return success_response(
        data=CommentResponse(
            id=comment.id,
            dataset_id=comment.dataset_id,
            video_id=comment.video_id,
            title=comment.title,
            channel_name=comment.channel_name,
            date=comment.date,
            author=comment.author,
            comment=comment.comment,
            label=comment.label,
            clean_comment=comment.clean_comment,
            predicted_label=comment.predicted_label,
            source=comment.source.value,
            source_detail=comment.source_detail,
            created_at=comment.created_at,
        ),
        message=f"Comment {comment_id} manually labeled as {'judi' if payload.label == '1' else 'non judi'}",
    )


@router.delete("/comment/{comment_id}/label", response_model=APIResponse)
async def reset_manual_label(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Reset label manual ke null (kembali hanya pakai predicted_label)."""
    repo = CommentRepository(db)
    comment = await repo.update_label(comment_id, None)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    await db.commit()
    return success_response(message=f"Manual label for comment {comment_id} has been reset")


@router.patch("/dataset/{dataset_id}/bulk", response_model=APIResponse)
async def bulk_manual_label(
    dataset_id: int,
    payload: BulkManualLabelRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """
    Koreksi label manual untuk banyak comment sekaligus dalam satu dataset.
    Hanya comment yang ada di dataset tersebut yang akan diupdate.
    """
    repo = CommentRepository(db)

    # Filter only comment_ids that belong to this dataset
    all_ids = {item.comment_id for item in payload.labels}
    valid_comments = await db.execute(
        select(Comment.id).where(
            Comment.dataset_id == dataset_id,
            Comment.id.in_(all_ids),
        )
    )
    valid_ids = {row[0] for row in valid_comments.all()}

    updates = [
        {"comment_id": item.comment_id, "label": item.label}
        for item in payload.labels
        if item.comment_id in valid_ids
    ]
    skipped = len(payload.labels) - len(updates)

    updated = await repo.bulk_update_labels(updates)
    await db.commit()

    return success_response(
        data=BulkManualLabelResponse(updated_count=updated, skipped_count=skipped),
        message=f"{updated} comments updated, {skipped} skipped (not in dataset)",
    )
