import logging
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, Optional, TypedDict, Literal
from app.models.llm_model import LLMModel
from app.services.eah_agent.core.agent_nlu import IntentResult

# 定义统一的输出类型，增强代码提示和健壮性
class StreamResponse(TypedDict):
    type: Literal["content", "think", "status", "error", "tool_start", "tool_end", "run_output"]
    content: Optional[Any]
    data: Optional[Any]

class BaseHandler(ABC):
    """
    Abstract base class for all agent handlers (Quick, Plan, Team, Flow).
    核心功能：
    1. 定义统一的处理接口（process方法）。
    2. 支持不同的LLM模型。
    3. 提供基础的日志记录功能。
    """

    def __init__(self, llm_model: Optional[LLMModel] = None):
        self.llm_model = llm_model
        # 自动获取子类的名称作为日志标识
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def process(
        self, 
        input_text: str, 
        intent: IntentResult, 
        **kwargs
    ) -> AsyncGenerator[StreamResponse, None]:
        """
        Processes the user input based on the handler's logic.
        
        Args:
            input_text: 用户原始输入字符串
            intent: NLU 解析后的意图对象
            **kwargs: 额外参数（如 session_id, history, user_info 等）

        Yields:
            StreamResponse: 包含类型和内容的字典
        """
        # 在这里可以写一些通用的逻辑，或者直接 pass
        if False: yield  # 只是为了让编辑器知道这是一个生成器
        pass

    def _log_error(self, error: Exception):
        """通用的错误日志记录"""
        self.logger.error(f"Error processing request: {str(error)}", exc_info=True)