from datetime import datetime
from typing import Optional

from pydantic import BaseModel

class KnowledgeBaseBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: Optional[str] = "active"

class KnowledgeBaseCreate(KnowledgeBaseBase):
    pass

class KnowledgeBaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class KnowledgeBaseResponse(KnowledgeBaseBase):
    id: str
    file_count: int
    folder_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
