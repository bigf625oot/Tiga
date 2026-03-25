import logging
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, Optional

from app.models.llm_model import LLMModel
from app.services.eah_agent.core.agent_nlu import IntentResult
from app.services.eah_agent.core.components.default_memory_manager import DefaultMemoryManager

class LightBaseExecutor(ABC):
    """
    轻量级基类 (Light Executor)。
    主要用于 Quick 模式等不需要复杂规划与反思的场景。
    只包含最基础的模型依赖和记忆管理（上下文加载），从而保证极低的延迟。
    """
    
    def __init__(
        self,
        llm_model: Optional[LLMModel] = None,
        memory_manager: Optional[DefaultMemoryManager] = None,
    ):
        self.llm_model = llm_model
        self.memory_manager = memory_manager
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def execute(
        self,
        input_text: str,
        intent: IntentResult,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        核心执行流：由子类实现简单的 Prompt 组装、单次 LLM 调用和流式输出。
        """
        pass
