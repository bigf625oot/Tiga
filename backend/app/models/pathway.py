from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.db.base import Base

class PathwayJobStatus(str, enum.Enum):
    CREATED = "created"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"

class PathwaySource(Base):
    __tablename__ = "pathway_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    type = Column(String, nullable=False) # kafka, postgres, mysql, generic_sql, s3, rest
    
    # Configuration JSON (host, port, topic, query, etc.)
    # Sensitive fields like password should be encrypted before storage if possible, 
    # or stored in separate encrypted columns. For simplicity, we assume 'config' stores 
    # non-sensitive data and 'secrets' stores encrypted credentials.
    config = Column(JSON, nullable=False, default={}) 
    secrets_encrypted = Column(Text, nullable=True) # JSON string encrypted with Fernet
    
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    jobs = relationship("PathwayJob", back_populates="source")

class PathwayJob(Base):
    __tablename__ = "pathway_jobs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    
    source_id = Column(Integer, ForeignKey("pathway_sources.id"), nullable=False)
    source = relationship("PathwaySource", back_populates="jobs")
    
    # Operator and Sink configuration
    operators_config = Column(JSON, nullable=False, default=[])
    sinks_config = Column(JSON, nullable=False, default=[])
    
    status = Column(String, default=PathwayJobStatus.CREATED)
    pid = Column(Integer, nullable=True) # Process ID if running locally
    
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
