import enum


class DataSource(str, enum.Enum):
    YOUTUBE_API = "youtube_api"
    KAGGLE = "kaggle"
    MANUAL = "manual"
