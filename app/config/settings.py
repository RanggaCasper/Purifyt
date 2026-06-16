from functools import lru_cache
import sys
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Purifyt - YouTube Comment Dataset API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # MySQL
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DATABASE: str = "purifyt"

    # YouTube API
    YOUTUBE_API_KEY: str = ""

    # Kaggle
    KAGGLE_USERNAME: str = ""
    KAGGLE_KEY: str = ""

    # JWT
    SECRET_KEY: str = "hL3dI1acL-HMATYwxpNW_9c_RNvYCy0kgYJ6Js3cPMY" # Change this
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Cookie / CORS
    COOKIE_SECURE: bool = False          # True in production (HTTPS)
    COOKIE_SAMESITE: str = "Lax"         # "None" if cross-domain + Secure=True
    COOKIE_DOMAIN: str | None = None     # e.g. ".example.com" for cross-domain
    CORS_ORIGINS: list[str] = [
        "*"
    ]

    @property
    def IS_COMPILED(self) -> bool:
        return bool(getattr(sys, "frozen", False))

    @property
    def SQLITE_DATABASE_PATH(self) -> Path:
        if self.IS_COMPILED:
            return Path(sys.executable).resolve().parent / "purifyt.db"
        return Path("purifyt.db").resolve()

    @property
    def DATABASE_URL(self) -> str:
        if self.IS_COMPILED:
            return f"sqlite+aiosqlite:///{self.SQLITE_DATABASE_PATH.as_posix()}"

        return (
            f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
        )

    @property
    def SYNC_DATABASE_URL(self) -> str:
        if self.IS_COMPILED:
            return f"sqlite:///{self.SQLITE_DATABASE_PATH.as_posix()}"

        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
        )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
