from datetime import datetime
from typing import Optional, Any, List
from pydantic import BaseModel

class AgentWorkflowBase(BaseModel):
    name: str
    description: Optional[str] = None
    definition: Optional[Any] = None
    tags: Optional[List[str]] = None
    is_active: bool = True

class AgentWorkflowCreate(AgentWorkflowBase):
    pass

class AgentWorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    definition: Optional[Any] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None

class AgentWorkflowResponse(AgentWorkflowBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
