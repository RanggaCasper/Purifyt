from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Token(BaseModel):
    """JSON body returned on login / refresh (no refresh_token here!)."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    username: Optional[str] = None


class LoginRequest(BaseModel):
    """Accepts username + password."""
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6)


class UserResponse(BaseModel):
    id: int
    username: str
    created_at: datetime

    class Config:
        from_attributes = True
