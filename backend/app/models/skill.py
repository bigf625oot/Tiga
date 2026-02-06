import uuid

from sqlalchemy import JSON, Boolean, Column, DateTime, String, Text
from sqlalchemy.sql import func

from app.db.base import Base


class Skill(Base):
    __tablename__ = "skills"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    version = Column(String, default="1.0.0")

    # Core content
    content = Column(Text, nullable=True)  # The prompt/instruction
    tools_config = Column(JSON, nullable=True)  # Specific tools required by this skill

    # Metadata
    meta_data = Column(JSON, nullable=True)  # { "author": "...", "tags": [...], "compatibility": "..." }

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
