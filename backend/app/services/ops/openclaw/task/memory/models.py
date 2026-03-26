"""
Agent Memory Data Models

Defines the core data structures for the Agent Memory module.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import uuid

class MemoryType(str, Enum):
    CONVERSATION = "conversation"
    TASK_RESULT = "task_result"
    OBSERVATION = "observation"
    REFLECTION = "reflection"

class MemoryUnit(BaseModel):
    """
    A single unit of memory (e.g., a chat message, a task output).
    Stored as JSON in Redis.
    """
    memory_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    type: MemoryType
    content: str  # The actual text content
    metadata: Dict[str, Any] = Field(default_factory=dict) # Structured data (e.g., task_id, params)
    created_at: float = Field(default_factory=lambda: datetime.now().timestamp())
    ttl: Optional[int] = None # Seconds to live

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v):
        if not v:
            raise ValueError("session_id cannot be empty")
        return v

class MemoryIndex(BaseModel):
    """
    Metadata for searching/indexing memories.
    """
    memory_id: str
    session_id: str
    embedding: Optional[List[float]] = None # Vector embedding
    keywords: List[str] = Field(default_factory=list) # Extracted keywords for BM25
    timestamp: float

class SessionContext(BaseModel):
    """
    Aggregated context for a session.
    """
    session_id: str
    recent_memories: List[MemoryUnit]
    summary: Optional[str] = None
    last_active: float
