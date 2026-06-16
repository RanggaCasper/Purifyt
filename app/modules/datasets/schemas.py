from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class CommentBase(BaseModel):
    video_id: str
    title: Optional[str] = None
    channel_name: Optional[str] = None
    date: Optional[datetime] = None
    author: Optional[str] = None
    comment: Optional[str] = None
    label: Optional[str] = None
    clean_comment: Optional[str] = None
    predicted_label: Optional[str] = None


class CommentCreate(CommentBase):
    dataset_id: int


class CommentResponse(CommentBase):
    id: int
    dataset_id: int
    source: str
    source_detail: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DatasetCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None


class DatasetResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    source: str
    source_url: Optional[str]
    owner_id: Optional[int]
    created_at: datetime
    comment_count: Optional[int] = 0

    class Config:
        from_attributes = True


class DatasetDetailResponse(DatasetResponse):
    comments: List[CommentResponse] = []


class PaginatedResponse(BaseModel):
    total: int
    page: int
    per_page: int
    items: List


class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None
