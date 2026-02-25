
import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class DataQuerySession(Base):
    __tablename__ = "data_query_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(255), nullable=True) # Assuming authentication might be added later or is optional
    title = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_archived = Column(Boolean, default=False)
    is_pinned = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    messages = relationship("DataQueryMessage", back_populates="session", cascade="all, delete-orphan")

class DataQueryMessage(Base):
    __tablename__ = "data_query_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), ForeignKey("data_query_sessions.id"), nullable=False)
    role = Column(String(50), nullable=False) # 'user' or 'assistant'
    content = Column(Text, nullable=True) # Natural language query or answer
    sql_query = Column(Text, nullable=True) # Generated SQL
    chart_config = Column(JSON, nullable=True) # ECharts option JSON
    error_message = Column(Text, nullable=True) # Error details if any
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("DataQuerySession", back_populates="messages")
