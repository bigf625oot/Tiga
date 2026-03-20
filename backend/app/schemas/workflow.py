from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel


class WorkflowBase(BaseModel):
    name: str
    description: Optional[str] = None
    webhook_url: Optional[str] = None # Make optional to support definition based workflows
    definition: Optional[Dict[str, Any]] = None
    is_active: bool = True
    is_latest: bool = True
    is_draft: bool = False
    version: int = 1
    change_log: Optional[str] = None
    input_variables: Optional[Dict[str, Any]] = None
    runtime_config: Optional[Dict[str, Any]] = None


class WorkflowCreate(WorkflowBase):
    original_id: Optional[str] = None # For creating new version


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    webhook_url: Optional[str] = None
    definition: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_latest: Optional[bool] = None
    is_draft: Optional[bool] = None
    change_log: Optional[str] = None
    input_variables: Optional[Dict[str, Any]] = None
    runtime_config: Optional[Dict[str, Any]] = None


class WorkflowResponse(WorkflowBase):
    id: str
    original_id: str
    user_id: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
