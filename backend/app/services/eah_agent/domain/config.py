"""
Agent and Tool Configuration Models
核心功能：
- 定义智能体（Agent）和工具（Tool）的配置模型
- 支持工具的启用/禁用和自定义配置
- 定义智能体的角色、指令、工具和技能
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ToolConfig(BaseModel):
    name: str = Field(..., description="Name of the tool/skill")
    enabled: bool = Field(True, description="Whether the tool is enabled")
    config: Dict[str, Any] = Field(default_factory=dict, description="Configuration for the tool")

class AgentConfig(BaseModel):
    name: str = Field(..., description="Name of the agent")
    role: str = Field(..., description="Role description of the agent")
    instructions: List[str] = Field(default_factory=list, description="List of instructions")
    tools: List[ToolConfig] = Field(default_factory=list, description="List of tools to enable")
    skills: List[str] = Field(default_factory=list, description="List of skills to enable (names only)")
    model_id: Optional[str] = Field(None, description="Specific model ID to use")
    model_params: Dict[str, Any] = Field(default_factory=dict, description="Model parameters (e.g., temperature, max_tokens)")
    reasoning: bool = Field(False, description="Enable reasoning/Chain-of-Thought")
    
class TeamConfig(BaseModel):
    name: str = Field(..., description="Name of the team")
    leader_agent: AgentConfig = Field(..., description="Leader/Router agent configuration")
    members: List[AgentConfig] = Field(..., description="Team member agents")
