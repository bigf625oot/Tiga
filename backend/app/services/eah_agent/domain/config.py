from typing import List, Optional, Dict, Any, Union, Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator

# --- 1. 核心基类：消除元数据重复 ---
class BaseNode(BaseModel):
    """所有配置实体的原子基类"""
    model_config = ConfigDict(extra='allow', populate_by_name=True)

    name: str = Field(..., description="名称")
    description: Optional[str] = Field(None, description="描述/简介")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="运行时扩展元数据")

# --- 2. 模型设置：将“大脑配置”抽离 ---
class LLMSettings(BaseModel):
    """模型参数配置（独立于 Agent 身份）"""
    model_id: str = Field("gpt-4-turbo")
    temperature: float = Field(0.7, ge=0, le=2.0)
    max_tokens: Optional[int] = None
    reasoning: bool = False
    extra_params: Dict[str, Any] = Field(default_factory=dict, description="透传给底层的参数")

# --- 3. 具体的组件实现 ---

class ToolConfig(BaseNode):
    """工具配置：继承基础属性 + 状态"""
    enabled: bool = Field(True)
    plugin_type: Optional[str] = None
    # 统一使用 settings 代替原来的 config/model_params
    settings: Dict[str, Any] = Field(default_factory=dict)

class AgentConfig(BaseNode):
    """单智能体：组合了身份、大脑、工具"""
    role: str = Field(..., description="角色定位")
    instructions: List[str] = Field(default_factory=list)
    
    # 组合模型配置
    llm: LLMSettings = Field(default_factory=LLMSettings)
    
    # 组合工具配置 (允许实例化工具或配置字典)
    tools: List[Any] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    memory_enabled: bool = True

    @field_validator('instructions', mode='before')
    @classmethod
    def ensure_list(cls, v):
        if isinstance(v, str): return [v]
        return v

class TeamConfig(BaseNode):
    """团队配置：领导者与成员的递归组合"""
    team_id: str = Field(...)
    strategy: Literal["orchestration", "sequential", "autonomous"] = "orchestration"
    
    leader: AgentConfig = Field(..., description="领导者")
    members: List[AgentConfig] = Field(default_factory=list, description="执行成员")
    
    max_loops: int = 10
    shared_storage: bool = True