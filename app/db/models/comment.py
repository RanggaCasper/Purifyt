from datetime import datetime

from sqlalchemy import Column, DateTime, Enum as SAEnum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.connection import Base
from app.db.models.common import DataSource


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
    source_detail = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    dataset = relationship("Dataset", back_populates="comments")

    __table_args__ = (
        Index("ix_comments_video_id_author", "video_id", "author"),
    )
