from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    """JSON body returned on login / refresh (no refresh_token here!)."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until access_token expires


class TokenData(BaseModel):
    username: Optional[str] = None


class LoginRequest(BaseModel):
    """Accepts email OR username + password."""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: str = Field(..., min_length=1)


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
    video_id: Optional[str] = Field(None, description="Specific video ID to fetch comments from")
    query: Optional[str] = Field(None, description="Search query to find a video (used if video_id is not provided)")
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


class ScannedComment(BaseModel):
    author: Optional[str] = None
    commentId: Optional[str] = None
    comment: Optional[str] = None
    clean_comment: Optional[str] = None
    predicted_label: int  # 0 = normal, 1 = judi online
    confidence_normal: float
    confidence_judi: float


class YouTubeScanResponse(BaseModel):
    video_id: str
    title: Optional[str] = None
    channel_name: Optional[str] = None
    total_comments: int
    judi_count: int
    normal_count: int
    comments: List[ScannedComment]
