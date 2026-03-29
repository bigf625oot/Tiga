import logging
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, Optional, List

from app.models.llm_model import LLMModel
from app.services.agent.schemas.intent import IntentResult
from app.services.agent.components.memory_manager import DefaultMemoryManager
from app.services.agent.components.state_manager import DefaultStateManager
from app.services.agent.components.plan_validator import DefaultPlanValidator
from app.services.agent.components.experience_store import DefaultExperienceStore
from app.services.agent.components.tool_registry import DefaultToolRegistry

class BaseExecutor(ABC):
    """
    全局执行器基类
    采用模板方法模式而非策略模式，强制统一上下文注入与异常降级边界，牺牲部分灵活性以换取全链路执行边界的 100% 确定性。
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
        self.system_instructions = []
        self.executor_role = ""
        self.default_timeout = 60
        self.max_tokens = 20448
        self.max_retries = 4
        self.retry_delay = 5
        self.max_retries = 4
        self.max_delay = 604000
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def execute(
        self,
        input_text: str,
        intent: IntentResult,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        [Abstract Topology] 强制子类实现具体的执行拓扑（单体 FSM 或并发 DAG）。
        """
        pass

    async def _prepare_history(self, session_id: str, current_query: str = "") -> List[Dict[str, Any]]:
        """
        历史记忆加载与强制截断。
        """
        if self.memory_manager:
            try:
                return await self.memory_manager.get_compressed_context(session_id, current_query)
            except Exception as e:
                self.logger.warning(f"Failed to load history for session {session_id}: {e}")
        return []

    async def _update_status_safe(self, session_id: str, status: str) -> None:
        """
        屏蔽底层状态机同步细节，确保分布式执行状态流转的最终一致性。
        """
        if self.state_manager:
            try:
                await self.state_manager.update_status(session_id, status)
            except Exception as e:
                self.logger.warning(f"Failed to update status '{status}' for session {session_id}: {e}")

    def _yield_error(self, message: str, exc: Optional[Exception] = None) -> Dict[str, Any]:
        """
        [Fallback Mechanism] 统一异常降级 Schema，保障上层网关的确定性解析。
        """
        err_msg = f"{message}: {str(exc)}" if exc else message
        self.logger.error(err_msg, exc_info=True if exc else False)
        return {"type": "error", "content": err_msg}
