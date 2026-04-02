import logging
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, Optional, List

from app.models.llm_model import LLMModel
from app.services.agent.schemas.intent import IntentResult
from app.services.agent.components.memory_manager import DefaultMemoryManager

class LightBaseExecutor(ABC):
    """
    轻量级执行器基类
    彻底剥离规划(Planning)与反思(Reflection)等重型认知链路，牺牲复杂任务处理能力，换取极低延迟与 O(1) 的执行复杂度。仅保留核心的模型依赖与上下文加载能力。
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
        [Constraint] 强制子类实现单一职责(Prompt->LLM->Stream)，禁止引入复杂状态机，保证执行流 100% 可预测。
        """
        pass

    async def _prepare_history(self, session_id: str, current_query: str = "") -> List[Dict[str, Any]]:
        """
        [Context Control] 强制历史压缩与截断，防止 Token 逃逸与 OOM。
        """
        if self.memory_manager:
            try:
                return await self.memory_manager.get_compressed_context(session_id, current_query)
            except Exception as e:
                self.logger.warning(f"Failed to load history for session {session_id}: {e}")
        return []

    def _yield_error(self, message: str, exc: Optional[Exception] = None) -> Dict[str, Any]:
        """
        [Fallback] 统一异常降级 Schema，保障上层网关解析确定性。
        """
        err_msg = f"{message}: {str(exc)}" if exc else message
        self.logger.error(err_msg, exc_info=True if exc else False)
        return {"type": "error", "content": err_msg}
