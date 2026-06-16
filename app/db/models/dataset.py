from datetime import datetime

from sqlalchemy import Column, DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.connection import Base
from app.db.models.common import DataSource


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
