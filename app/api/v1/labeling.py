"""Auto-labeling endpoints using the judi/normal classification model."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.connection import get_db
from app.db.models import Comment
from app.db.repositories.comment_repository import CommentRepository
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
