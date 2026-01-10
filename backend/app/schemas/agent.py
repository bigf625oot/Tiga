from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class AgentBase(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = "robot"
    system_prompt: Optional[str] = None
    # Rename field to avoid conflict with Pydantic protected namespace 'model_'
    # And we CANNOT use 'model_config' as variable name in Pydantic V2 class body 
    # because it conflicts with the ConfigDict 'model_config'.
    # So we use 'agent_model_config' and alias it to 'model_config' for JSON serialization.
    agent_model_config: Optional[Dict[str, Any]] = Field(default_factory=dict, alias="model_config")
    tools_config: Optional[List[str]] = None
    mcp_config: Optional[List[Dict[str, Any]]] = None
    skills_config: Optional[Dict[str, Any]] = None
    knowledge_config: Optional[Dict[str, Any]] = None
    memory_config: Optional[Dict[str, Any]] = None
    storage_config: Optional[Dict[str, Any]] = None
    is_active: bool = True
    is_template: bool = False
    
    # Use Pydantic V2 ConfigDict
    model_config = {
        "populate_by_name": True
    }

class AgentCreate(AgentBase):
    pass

class AgentUpdate(AgentBase):
    name: Optional[str] = None
    is_active: Optional[bool] = None

class AgentResponse(AgentBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
