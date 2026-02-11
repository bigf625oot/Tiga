import enum
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Enum, Integer, String, Text, Boolean

from app.db.base import Base


class DocumentStatus(str, enum.Enum):
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    INDEXING = "indexing"
    INDEXED = "indexed"
    FAILED = "failed"


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    oss_key = Column(String)
    oss_url = Column(String)
    file_size = Column(Integer)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.UPLOADING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    error_message = Column(String, nullable=True)
    is_folder = Column(Boolean, default=False)
    parent_id = Column(Integer, nullable=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)


class KnowledgeChat(Base):
    __tablename__ = "knowledge_chats"

    id = Column(Integer, primary_key=True, index=True)
    doc_id = Column(Integer, index=True)
    role = Column(String)  # 'user' or 'assistant'
    content = Column(Text)
    sources = Column(JSON, nullable=True)
    session_id = Column(String, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
