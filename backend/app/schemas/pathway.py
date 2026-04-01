from typing import Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime

class ScheduleConfig(BaseModel):
    enabled: bool = False
    type: Optional[Literal["interval", "cron"]] = None
    value: Optional[str] = None
    description: Optional[str] = None
    next_run_at: Optional[datetime] = None

# Shared with models.py but using Pydantic for API
class PipelineCreate(BaseModel):
    name: str
    description: Optional[str] = None
    dag_config: Dict[str, Any] = Field(..., description="DAG JSON structure with nodes and edges")
    schedule_config: Optional[ScheduleConfig] = None

class PipelineUpdate(BaseModel):
    dag_config: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    schedule_config: Optional[ScheduleConfig] = None

class PipelineResponse(BaseModel):
    id: int
    name: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_run_at: Optional[datetime] = None # Derived or stored
    description: Optional[str] = None
    dag_config: Optional[Dict[str, Any]] = None
    schedule_config: Optional[ScheduleConfig] = None

    class Config:
        from_attributes = True

class PipelineRunResponse(BaseModel):
    pipeline_id: int
    status: str
    message: str
