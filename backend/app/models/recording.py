from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.db.base import Base


class Recording(Base):
    __tablename__ = "recordings"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    s3_key = Column(String, unique=True, index=True, nullable=True)  # Nullable for folders
    duration = Column(Integer, default=0)  # in seconds
    file_size = Column(Integer, default=0)  # in bytes
    format = Column(String, nullable=True)  # mp3, wav, or folder

    is_folder = Column(Boolean, default=False)
    parent_id = Column(Integer, nullable=True, index=True)  # For nested structure

    # Status fields for each stage
    upload_status = Column(String, default="pending")  # pending, completed, failed
    asr_status = Column(String, default="pending")  # pending, processing, completed, failed
    summary_status = Column(String, default="pending")  # pending, processing, completed, failed
    recommendation_status = Column(String, default="pending")  # pending, processing, completed, failed

    transcription_text = Column(Text, nullable=True)
    summary_text = Column(Text, nullable=True)
    recommendation_text = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
