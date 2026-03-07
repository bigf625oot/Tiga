from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

# Shared with models.py but using Pydantic for API
class PipelineCreate(BaseModel):
    name: str
    description: Optional[str] = None
    dag_config: Dict[str, Any] = Field(..., description="DAG JSON structure with nodes and edges")

class PipelineUpdate(BaseModel):
    dag_config: Optional[Dict[str, Any]] = None
    description: Optional[str] = None

class PipelineResponse(BaseModel):
    id: int
    name: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_run_at: Optional[datetime] = None # Derived or stored
    description: Optional[str] = None
    dag_config: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class PipelineRunResponse(BaseModel):
    pipeline_id: int
    status: str
    message: str
