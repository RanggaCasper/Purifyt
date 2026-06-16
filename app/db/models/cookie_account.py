from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from app.db.connection import Base


class CookieAccount(Base):
    """Stores YouTube cookie account info (multi-account support)."""
    __tablename__ = "cookie_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    channel_name = Column(String(255), nullable=True)
    cookie_path = Column(String(500), nullable=False)
    cookie_count = Column(Integer, default=0)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
