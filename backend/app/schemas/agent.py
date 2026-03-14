from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from app.core.i18n import _


class AgentBase(BaseModel):
    name: str = Field(..., description=_("The name of the agent"))
    description: Optional[str] = Field(None, description=_("A brief description of the agent's purpose"))
    icon: Optional[str] = Field("/tiga.svg", description=_("URL or path to the agent's icon"))
    category: Optional[str] = Field(None, description=_("The category of the agent"))
    system_prompt: Optional[str] = Field(None, description=_("The system prompt that defines the agent's behavior"))
    enable_react: bool = Field(True, description=_("Enable ReACT reasoning and acting (Framework level)"))
    enable_cot: bool = Field(True, description=_("Enable Chain of Thought prompt injection"))
    # Rename field to avoid conflict with Pydantic protected namespace 'model_'
    # And we CANNOT use 'model_config' as variable name in Pydantic V2 class body
    # because it conflicts with the ConfigDict 'model_config'.
    # So we use 'agent_model_config' and alias it to 'model_config' for JSON serialization.
    agent_model_config: Optional[Dict[str, Any]] = Field(default_factory=dict, alias="model_config", description=_("Configuration for the LLM model"))
    tools_config: Optional[List[Any]] = Field(None, description=_("List of tools enabled for this agent"))
    mcp_config: Optional[List[Dict[str, Any]]] = Field(None, description=_("Configuration for MCP (Model Context Protocol) servers"))
    skills_config: Optional[Dict[str, Any]] = Field(None, description=_("Configuration for agent skills"))
    knowledge_config: Optional[Dict[str, Any]] = Field(None, description=_("Configuration for knowledge base access"))
    memory_config: Optional[Dict[str, Any]] = Field(None, description=_("Configuration for agent memory"))
    storage_config: Optional[Dict[str, Any]] = Field(None, description=_("Configuration for storage"))
    is_active: bool = Field(True, description=_("Whether the agent is active"))
    is_template: bool = Field(False, description=_("Whether this agent is a template"))

    # Use Pydantic V2 ConfigDict
    model_config = {"populate_by_name": True}


class AgentCreate(AgentBase):
    pass


class AgentUpdate(AgentBase):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    enable_react: Optional[bool] = None
    enable_cot: Optional[bool] = None


class AgentClone(BaseModel):
    name: Optional[str] = Field(None, description=_("The name of the new agent"))
    is_template: bool = Field(False, description=_("Whether the new agent is a template"))


class AgentResponse(AgentBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
