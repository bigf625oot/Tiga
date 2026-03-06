from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TaskBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    status: str = "open"
    priority: int = Field(3, ge=1, le=5)
    assignee_id: Optional[str] = None


class TaskCreate(TaskBase):
    created_by: Optional[str] = None


class TaskUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    assignee_id: Optional[str] = None
    change_summary: Optional[str] = Field(None, max_length=500)
    actor_id: Optional[str] = None


class TaskStatusChange(BaseModel):
    status: str
    actor_id: Optional[str] = None
    note: Optional[str] = Field(None, max_length=500)


class TaskResponse(TaskBase):
    id: str
    created_by: Optional[str] = None
    current_version: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TaskVersionResponse(BaseModel):
    id: int
    task_id: str
    version: int
    name: str
    description: Optional[str] = None
    status: str
    priority: int
    assignee_id: Optional[str] = None
    changed_by: Optional[str] = None
    change_summary: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TaskQABase(BaseModel):
    question: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)
    user_id: Optional[str] = None


class TaskQACreate(TaskQABase):
    pass


class TaskQAUpdate(BaseModel):
    question: Optional[str] = Field(None, min_length=1)
    answer: Optional[str] = Field(None, min_length=1)
    user_id: Optional[str] = None


class TaskQAResponse(TaskQABase):
    id: int
    task_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TaskLogResponse(BaseModel):
    id: int
    task_id: str
    actor_id: Optional[str] = None
    action_type: str
    importance: str
    content: Optional[str] = None
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None
    created_at: datetime
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TaskBackupExport(BaseModel):
    exported_at: datetime
    tasks: List[Dict[str, Any]]
    versions: List[Dict[str, Any]]
    qas: List[Dict[str, Any]]
    logs: List[Dict[str, Any]]


class TaskBackupImportResult(BaseModel):
    tasks_created: int
    versions_created: int
    qas_created: int
    logs_created: int
