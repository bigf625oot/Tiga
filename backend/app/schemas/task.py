from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field, UUID4

class SubTaskBase(BaseModel):
    name: str
    task_type: str
    execution_order: int = 0
    dependencies: List[str] = []
    input_context: Optional[Dict[str, Any]] = None

class SubTaskCreate(SubTaskBase):
    pass

class SubTaskUpdate(BaseModel):
    status: Optional[str] = None
    output_result: Optional[Dict[str, Any]] = None
    worker_id: Optional[str] = None
    retry_count: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class SubTaskResponse(SubTaskBase):
    id: str
    parent_id: str
    status: str
    output_result: Optional[Dict[str, Any]] = None
    retry_count: int
    worker_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TaskBase(BaseModel):
    original_prompt: str
    priority: int = 1
    context: Optional[Dict[str, Any]] = None

class TaskCreate(TaskBase):
    user_id: Optional[str] = None

class TaskUpdate(BaseModel):
    status: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class TaskResponse(TaskBase):
    id: str
    user_id: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    sub_tasks: List[SubTaskResponse] = []

    class Config:
        from_attributes = True
