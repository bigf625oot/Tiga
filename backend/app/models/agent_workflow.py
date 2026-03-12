import uuid
from typing import List
from sqlalchemy import Boolean, Column, DateTime, String, JSON
from sqlalchemy.sql import func
from app.db.base import Base

class AgentWorkflow(Base):
    __tablename__ = "agent_workflows"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    definition = Column(JSON, nullable=True)  # Store flow structure (nodes, edges)
    tags = Column(JSON, nullable=True)  # Store tags for filtering
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
