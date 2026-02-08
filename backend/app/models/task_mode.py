import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.security import decrypt_json, decrypt_text
from app.db.base import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, index=True)
    description_enc = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="open", index=True)
    priority = Column(Integer, nullable=False, default=3, index=True)
    assignee_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    created_by = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    current_version = Column(Integer, nullable=False, default=1)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), index=True)

    versions = relationship("TaskVersion", back_populates="task", cascade="all, delete-orphan")
    qas = relationship("TaskQA", back_populates="task", cascade="all, delete-orphan")
    logs = relationship("TaskLog", back_populates="task", cascade="all, delete-orphan")

    @property
    def description(self):
        return decrypt_text(self.description_enc)


class TaskVersion(Base):
    __tablename__ = "task_versions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False, index=True)
    version = Column(Integer, nullable=False, index=True)

    name = Column(String, nullable=False)
    description_enc = Column(Text, nullable=True)
    status = Column(String, nullable=False)
    priority = Column(Integer, nullable=False)
    assignee_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)

    changed_by = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    change_summary = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    task = relationship("Task", back_populates="versions")

    __table_args__ = (Index("ix_task_versions_task_version", "task_id", "version", unique=True),)

    @property
    def description(self):
        return decrypt_text(self.description_enc)


class TaskQA(Base):
    __tablename__ = "task_qas"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)

    question_enc = Column(Text, nullable=False)
    answer_enc = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), index=True)

    task = relationship("Task", back_populates="qas")

    @property
    def question(self):
        return decrypt_text(self.question_enc)

    @property
    def answer(self):
        return decrypt_text(self.answer_enc)


class TaskLog(Base):
    __tablename__ = "task_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False, index=True)
    actor_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)

    action_type = Column(String, nullable=False, index=True)
    importance = Column(String, nullable=False, default="normal", index=True)

    content_enc = Column(Text, nullable=True)
    before_state_enc = Column(Text, nullable=True)
    after_state_enc = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)

    task = relationship("Task", back_populates="logs")

    @property
    def content(self):
        return decrypt_text(self.content_enc)

    @property
    def before_state(self):
        return decrypt_json(self.before_state_enc)

    @property
    def after_state(self):
        return decrypt_json(self.after_state_enc)
