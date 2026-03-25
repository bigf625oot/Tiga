import logging
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, Optional, List

from app.models.llm_model import LLMModel
from app.services.eah_agent.schemas.intent import IntentResult
from app.services.eah_agent.components.memory_manager import DefaultMemoryManager

class LightBaseExecutor(ABC):
    """
    轻量级执行器基类 (Light Executor)
    
    [设计哲学 & Trade-offs]
    采用极简架构，彻底剥离规划(Planning)与反思(Reflection)等重型认知链路，专为 Quick 模式等对延迟极度敏感的场景打造。
    权衡：牺牲了处理复杂多步任务的能力，换取极低的系统延迟和确定性的执行耗时。
    仅保留核心的模型依赖与上下文加载能力，确保核心链路的纯粹性。
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
        核心执行流规约接口
        
        [设计意图]
        强制子类实现单一职责的执行流（Prompt组装 -> 单次LLM调用 -> 流式输出）。
        禁止在此处引入复杂的状态机或循环分支，保持 O(1) 的执行流复杂度，确保行为的 100% 可预测性。
        """
        pass

    async def _prepare_history(self, session_id: str, current_query: str = "") -> List[Dict[str, Any]]:
        """
        上下文边界控制方法
        
        [设计意图]
        将记忆管理的职责从具体执行器中解耦。通过 MemoryManager 强制进行历史消息的压缩与截断，
        防止因上下文无限增长导致的 OOM 或 Token 逃逸，为底层 LLM 调用提供确定性的输入边界。
        """
        if self.memory_manager:
            try:
                return await self.memory_manager.get_compressed_context(session_id, current_query)
            except Exception as e:
                self.logger.warning(f"Failed to load history for session {session_id}: {e}")
        return []

    def _yield_error(self, message: str, exc: Optional[Exception] = None) -> Dict[str, Any]:
        """
        异常降级标准化出口
        
        [设计意图]
        收拢所有执行器子类的异常抛出格式，输出统一的 Schema 事件。为上层网关或调用方提供
        结构化、可预期的降级数据结构，避免因异常处理碎片化导致的全链路崩溃。
        """
        err_msg = f"{message}: {str(exc)}" if exc else message
        self.logger.error(err_msg, exc_info=True if exc else False)
        return {"type": "error", "content": err_msg}
