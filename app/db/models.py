import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Enum as SAEnum, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from app.db.connection import Base


class DataSource(str, enum.Enum):
    YOUTUBE_API = "youtube_api"
    KAGGLE = "kaggle"
    MANUAL = "manual"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    datasets = relationship("Dataset", back_populates="owner")


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    source = Column(SAEnum(DataSource), nullable=False, default=DataSource.MANUAL)
    source_url = Column(String(500), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="datasets")
    comments = relationship("Comment", back_populates="dataset", cascade="all, delete-orphan")


class TokenBlacklist(Base):
    """Legacy blacklist – kept for backwards-compat; new auth uses RefreshToken."""
    __tablename__ = "token_blacklist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    jti = Column(String(36), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_type = Column(String(10), nullable=False)  # "access" or "refresh"
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class RefreshToken(Base):
    """
    Stores hashed refresh tokens for rotation & revocation.
    - token_hash: SHA-256 hex digest of the opaque token sent in the cookie
    - revoked_at: set when the token is rotated or explicitly logged-out
    - rotated_from_id: points to the previous RefreshToken after rotation
    """
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    rotated_from_id = Column(Integer, ForeignKey("refresh_tokens.id"), nullable=True)
    user_agent = Column(String(512), nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="refresh_tokens")


class AppSetting(Base):
    """Stores application-level configuration values in the database."""
    __tablename__ = "app_settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CookieAccount(Base):
    """Stores YouTube cookie account info (multi-account support)."""
    __tablename__ = "cookie_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    channel_name = Column(String(255), nullable=True)
    cookie_path = Column(String(500), nullable=False)
    cookie_count = Column(Integer, default=0)
    is_active = Column(Integer, default=1)  # 1 = active, 0 = inactive/expired
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    video_id = Column(String(50), nullable=False, index=True)
    title = Column(String(500), nullable=True)
    channel_name = Column(String(255), nullable=True)
    date = Column(DateTime, nullable=True)
    author = Column(String(255), nullable=True)
    comment = Column(Text, nullable=True)
    label = Column(String(100), nullable=True)
    clean_comment = Column(Text, nullable=True)
    predicted_label = Column(String(100), nullable=True)
    source = Column(SAEnum(DataSource), nullable=False, default=DataSource.MANUAL)
    source_detail = Column(String(500), nullable=True)  # e.g. kaggle dataset slug or youtube video URL
    created_at = Column(DateTime, default=datetime.utcnow)

    dataset = relationship("Dataset", back_populates="comments")

    __table_args__ = (
        Index("ix_comments_video_id_author", "video_id", "author"),
    )
