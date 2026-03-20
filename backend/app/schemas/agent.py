from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.core.i18n import _

class AgentBase(BaseModel):
    name: str = Field(..., description=_("The name of the agent"))
    description: Optional[str] = Field(None, description=_("A brief description of the agent's purpose"))
    icon: Optional[str] = Field("/agent/agent_1.svg", description=_("URL or path to the agent's icon"))
    category: Optional[str] = Field(None, description=_("The category of the agent"))
    
    # LLM Config
    provider: str = Field("openai", description=_("LLM provider name"))
    model_id: str = Field(..., description=_("The specific model identifier"))
    
    # Prompts
    system_prompt: Optional[str] = Field(None, description=_("The system prompt that defines the agent's behavior"))
    instructions: Optional[List[str]] = Field(None, description=_("Agno-specific instruction list"))
    
    # Framework Toggles
    enable_react: bool = Field(True, description=_("Enable ReACT reasoning and acting"))
    enable_cot: bool = Field(True, description=_("Enable Chain of Thought"))
    show_tool_calls: bool = Field(True, description=_("Show tool call trace in output"))
    enable_markdown: bool = Field(True, description=_("Force Markdown output rendering"))
    
    # Pydantic V2 restriction: Cannot use 'model_config' as field name. Use alias.
    agent_model_config: Optional[Dict[str, Any]] = Field(default_factory=dict, alias="model_config", description=_("Extra LLM model params"))
    
    # Extensions & Storage
    tools_config: Optional[List[Any]] = Field(None, description=_("List of enabled standard tools"))
    mcp_config: Optional[List[Dict[str, Any]]] = Field(None, description=_("MCP servers configuration"))
    skills_config: Optional[Dict[str, Any]] = Field(None, description=_("Agent skills configuration"))
    knowledge_config: Optional[Dict[str, Any]] = Field(None, description=_("Knowledge base configuration"))
    memory_config: Optional[Dict[str, Any]] = Field(None, description=_("Memory configuration"))
    storage_config: Optional[Dict[str, Any]] = Field(None, description=_("Storage configuration"))
    
    # Metadata
    role: str = Field("general", description=_("Agent role (e.g., planner, executor)"))
    is_active: bool = Field(True, description=_("Whether the agent is active"))
    is_template: bool = Field(False, description=_("Whether this agent is a template"))

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
