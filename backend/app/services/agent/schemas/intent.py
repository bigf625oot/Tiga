from typing import Any, Dict, Optional, Literal, List
from pydantic import BaseModel, Field, ConfigDict

# 定义三大底层架构范式
ParadigmType = Literal["lite", "agentic", "specialized"]

class IntentResult(BaseModel):
    """意图识别结果模型"""
    model_config = ConfigDict(extra='ignore')
    
    intent: str = Field(..., description="识别出的细分意图类别 (如 chat, task, team, data_query 等)")
    paradigm: ParadigmType = Field(default="lite", description="宏观执行范式 (lite: 对话流, agentic: 复杂状态机/工作流, specialized: 领域编译器)")
    confidence: float = Field(default=1.0, description="置信度")
    reasoning: Optional[str] = Field(default="", description="推理过程")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="提取的参数")
    suggested_tools: List[str] = Field(default_factory=list, description="通过 NLU 或 Tools RAG 动态推荐的工具标识符列表")
    
    @classmethod
    def resolve_paradigm(cls, intent: str) -> ParadigmType:
        """根据细分意图推导宏观范式 (降维打击)"""
        intent = intent.lower()
        if intent in ("task", "team", "workflow", "plan", "solo", "flow"):
            return "agentic"
        elif intent in ("data_query", "kg_qa", "data", "kg"):
            return "specialized"
        return "lite"
