from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


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


class YouTubeSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query for YouTube")
    video_id: Optional[str] = Field(None, description="Specific video ID to fetch comments from")
    max_results: Optional[int] = Field(None, ge=1, description="Max comments to fetch (None = fetch all)")
    dataset_name: Optional[str] = Field(None, description="Name for the dataset (auto-generated if empty)")


class YouTubeVideoInfo(BaseModel):
    video_id: str
    title: str
    channel_name: str
    published_at: Optional[str] = None


class KaggleImportRequest(BaseModel):
    dataset_slug: str = Field(
        ...,
        description="Kaggle dataset slug, e.g. 'username/dataset-name'"
    )
    dataset_name: Optional[str] = Field(
        None,
        description="Name for the dataset (auto-generated if empty)"
    )


class PaginatedResponse(BaseModel):
    total: int
    page: int
    per_page: int
    items: List


class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None
