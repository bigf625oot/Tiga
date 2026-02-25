from datetime import datetime
from typing import List, Optional, Any
from sqlalchemy import Column, String, Integer, JSON, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.base import Base

def generate_uuid():
    return str(uuid.uuid4())

class ExecutionTask(Base):
    __tablename__ = "execution_tasks"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, nullable=True, index=True) # Optional for now
    original_prompt = Column(Text, nullable=False)
    status = Column(String, default="PENDING", index=True) # PENDING, PROCESSING, COMPLETED, FAILED
    priority = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    context = Column(JSON, nullable=True)

    sub_tasks = relationship("SubTask", back_populates="parent_task", cascade="all, delete-orphan")

class SubTask(Base):
    __tablename__ = "sub_tasks"

    id = Column(String, primary_key=True, default=generate_uuid)
    parent_id = Column(String, ForeignKey("execution_tasks.id"), nullable=False)
    name = Column(String, nullable=False)
    task_type = Column(String, nullable=False) # CODE_GEN, DATA_RETRIEVAL, API_CALL
    status = Column(String, default="PENDING", index=True) # PENDING, QUEUED, RUNNING, COMPLETED, FAILED
    execution_order = Column(Integer, default=0)
    dependencies = Column(JSON, default=list) # List of sub_task_ids
    input_context = Column(JSON, nullable=True)
    output_result = Column(JSON, nullable=True)
    retry_count = Column(Integer, default=0)
    worker_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    parent_task = relationship("ExecutionTask", back_populates="sub_tasks")
    execution_logs = relationship("ExecutionLog", back_populates="sub_task", cascade="all, delete-orphan")

class ExecutionLog(Base):
    __tablename__ = "execution_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    sub_task_id = Column(String, ForeignKey("sub_tasks.id"), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration_ms = Column(Integer, nullable=True)
    tokens_used = Column(Integer, default=0)
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    status = Column(String, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sub_task = relationship("SubTask", back_populates="execution_logs")

class ExecutionToolConfig(Base):
    __tablename__ = "execution_tools"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, unique=True, nullable=False)
    type = Column(String, nullable=False) # MCP, SKILL, NATIVE
    schema = Column(JSON, nullable=False)
    endpoint = Column(String, nullable=True)
    config = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    permission_level = Column(String, default="USER")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
