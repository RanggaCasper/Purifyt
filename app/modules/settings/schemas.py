from typing import Optional

from pydantic import BaseModel


class AppCredentialsRequest(BaseModel):
    youtube_api_key: Optional[str] = None
    kaggle_username: Optional[str] = None
    kaggle_key: Optional[str] = None


class AppCredentialsResponse(BaseModel):
    youtube_api_key: Optional[str] = None
    kaggle_username: Optional[str] = None
    kaggle_key: Optional[str] = None
    youtube_api_key_set: bool = False
    kaggle_username_set: bool = False
    kaggle_key_set: bool = False
