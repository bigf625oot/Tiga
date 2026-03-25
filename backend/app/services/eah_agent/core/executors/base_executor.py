import logging
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, Optional

from app.models.llm_model import LLMModel
from app.services.eah_agent.core.agent_nlu import IntentResult
from app.services.eah_agent.core.components.default_memory_manager import DefaultMemoryManager
from app.services.eah_agent.core.components.default_state_manager import DefaultStateManager
from app.services.eah_agent.core.components.default_plan_validator import DefaultPlanValidator
from app.services.eah_agent.core.components.default_experience_store import DefaultExperienceStore
from app.services.eah_agent.core.components.default_tool_registry import DefaultToolRegistry

class BaseExecutor(ABC):
    """
    重度闭环基类 (Heavy Executor)。
    支持 Single (原 Plan), Team, Workflow 等复杂模式。
    内建了对完整状态管理、多步规划、反思、记忆的依赖。
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
