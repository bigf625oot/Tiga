import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, Integer, String, Text

from app.db.base import Base

class KnowledgeBaseStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), index=True, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(KnowledgeBaseStatus), default=KnowledgeBaseStatus.ACTIVE)
    
    file_count = Column(Integer, default=0)
    folder_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
