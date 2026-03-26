from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict

class IntentResult(BaseModel):
    """意图识别结果模型"""
    model_config = ConfigDict(extra='ignore')
    
    intent: str = Field(..., description="识别出的意图类别")
    confidence: float = Field(default=1.0, description="置信度")
    reasoning: Optional[str] = Field(default="", description="推理过程")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="提取的参数")
