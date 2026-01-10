from sqlalchemy import Column, String, DateTime, Text, JSON, Boolean
from sqlalchemy.sql import func
from app.db.base import Base
import uuid

class Agent(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    icon = Column(String, nullable=True, default="robot")  # Icon name or URL
    
    # Configuration
    system_prompt = Column(Text, nullable=True)
    model_config = Column(JSON, nullable=True)  # { "model_id": "...", "parameters": ... }
    tools_config = Column(JSON, nullable=True)  # [ "duckduckgo", "calculator" ]
    mcp_config = Column(JSON, nullable=True) # List of MCP servers and their config
    skills_config = Column(JSON, nullable=True) # Detailed skills configuration
    knowledge_config = Column(JSON, nullable=True) # { "knowledge_base_ids": [...] }
    
    # Advanced
    memory_config = Column(JSON, nullable=True)
    storage_config = Column(JSON, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_template = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
