from typing import List, Optional

from pydantic import BaseModel, Field


class YouTubeSearchRequest(BaseModel):
    video_id: Optional[str] = Field(None, description="Specific video ID to fetch comments from")
    query: Optional[str] = Field(None, description="Search query to find a video (used if video_id is not provided)")
    dataset_name: Optional[str] = Field(None, description="Name for the dataset (auto-generated if empty)")


class YouTubeVideoInfo(BaseModel):
    video_id: str
    title: str
    channel_name: str
    published_at: Optional[str] = None


class ScannedComment(BaseModel):
    author: Optional[str] = None
    commentId: Optional[str] = None
    comment: Optional[str] = None
    clean_comment: Optional[str] = None
    predicted_label: int
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
