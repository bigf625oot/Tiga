import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, Optional, List

from app.models.llm_model import LLMModel
from app.services.eah_agent.schemas.intent import IntentResult
from app.services.eah_agent.components.memory_manager import DefaultMemoryManager
from app.services.eah_agent.components.state_manager import DefaultStateManager
from app.services.eah_agent.components.plan_validator import DefaultPlanValidator
from app.services.eah_agent.components.experience_store import DefaultExperienceStore
from app.services.eah_agent.components.tool_registry import DefaultToolRegistry

class BaseExecutor(ABC):
    """
    Base Executor
    """
    
    def __init__(
        self,
        llm_model: Optional[LLMModel] = None,
        memory_manager: Optional[DefaultMemoryManager] = None,
        state_manager: Optional[DefaultStateManager] = None,
        plan_validator: Optional[DefaultPlanValidator] = None,
        experience_store: Optional[DefaultExperienceStore] = None,
        tool_registry: Optional[DefaultToolRegistry] = None,
    ):
        self.llm_model = llm_model
        self.memory_manager = memory_manager
        self.state_manager = state_manager
        self.plan_validator = plan_validator
        self.experience_store = experience_store
        self.tool_registry = tool_registry
        
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def execute(
        self,
        input_text: str,
        intent: IntentResult,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        核心执行流：由子类实现具体的规划-执行-评估-反思大循环。
        """
        pass

    async def _prepare_history(self, session_id: str, current_query: str = "") -> List[Dict[str, Any]]:
        """
        通用辅助方法：通过 MemoryManager 加载并压缩历史消息。
        供子类在准备执行上下文时复用。
        """
        if self.memory_manager:
            try:
                return await self.memory_manager.get_compressed_context(session_id, current_query)
            except Exception as e:
                self.logger.warning(f"Failed to load history for session {session_id}: {e}")
        return []

    async def _update_status_safe(self, session_id: str, status: str) -> None:
        """
        通用辅助方法：安全地更新任务状态。
        """
        if self.state_manager:
            try:
                await self.state_manager.update_status(session_id, status)
            except Exception as e:
                self.logger.warning(f"Failed to update status '{status}' for session {session_id}: {e}")

    def _yield_error(self, message: str, exc: Optional[Exception] = None) -> Dict[str, Any]:
        """
        通用辅助方法：格式化错误输出事件。
        """
        err_msg = f"{message}: {str(exc)}" if exc else message
        self.logger.error(err_msg, exc_info=True if exc else False)
        return {"type": "error", "content": err_msg}
