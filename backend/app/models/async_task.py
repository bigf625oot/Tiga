from sqlalchemy import Column, String, Integer, JSON, DateTime, Text, Boolean, Index
from sqlalchemy.sql import func
import uuid

from app.db.base import Base


def generate_uuid():
    return str(uuid.uuid4())


class AsyncTask(Base):
    __tablename__ = "async_tasks"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False, index=True)
    task_type = Column(String, default="GENERAL", index=True)
    status = Column(String, default="PENDING", index=True)
    progress = Column(Integer, default=0)
    msg = Column(String, default="")
    step = Column(String, default="")
    priority = Column(Integer, default=1)
    user_id = Column(String, nullable=True, index=True)
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted = Column(Boolean, default=False)

    __table_args__ = (
        Index("ix_async_tasks_status_deleted", "status", "deleted"),
        Index("ix_async_tasks_user_created", "user_id", "created_at"),
    )


class AsyncTaskLog(Base):
    __tablename__ = "async_task_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    task_id = Column(String, nullable=False, index=True)
    percent = Column(Integer, default=0)
    status = Column(String, nullable=False)
    msg = Column(String, default="")
    step = Column(String, default="")
    extend = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_async_task_logs_task_created", "task_id", "created_at"),
    )