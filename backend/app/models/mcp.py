import uuid
from sqlalchemy import Column, String, JSON, DateTime, Boolean, Integer, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base

class MCPServer(Base):
    __tablename__ = "mcp_servers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    version = Column(String, default="1.0.0")
    type = Column(String, nullable=False)  # "stdio" or "sse"
    config = Column(JSON, nullable=False)  # Stores command, args, url, env, etc.
    
    # New fields
    category = Column(String, index=True, nullable=True) # slug of the category
    author = Column(String, default="User")
    is_official = Column(Boolean, default=False)
    downloads = Column(Integer, default=0)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
