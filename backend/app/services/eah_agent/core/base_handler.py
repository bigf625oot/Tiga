"""
Base class for all agent handlers (Quick, Plan, Team, Flow).
核心功能：
1. 定义统一的处理接口（process方法）。
2. 支持不同的LLM模型（通过构造函数传入）。
3. 提供基础的日志记录功能。
"""
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, Optional
from app.models.llm_model import LLMModel
from app.services.eah_agent.core.nlu import IntentResult

class BaseHandler(ABC):
    """
    Abstract base class for all agent handlers (Quick, Plan, Team, Flow).
    """

    def __init__(self, llm_model: Optional[LLMModel] = None):
        self.llm_model = llm_model

    @abstractmethod
    async def process(self, input_text: str, intent: IntentResult, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Processes the user input based on the handler's logic.
        Yields response chunks in a unified format:
        {
            "type": "content" | "think" | "status" | "error",
            "content": str | dict
        }
        """
        pass
