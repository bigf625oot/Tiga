import logging
from enum import Enum
from typing import Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.llm_model import LLMModel
from app.services.eah_agent.core.agent_nlu import NluService, IntentResult

logger = logging.getLogger("eah.core.router")

class ModeRouter:
    """
    负责接收请求、执行 NLU 意图分析，并将任务分发给相应的 Executor。
    目前已完成向 Executor 架构的迁移，旧的 Handler 逻辑已被移除。
    """
    
    def __init__(self, llm_model: Optional[LLMModel] = None):
        self.llm_model = llm_model
        
    async def route_request(self, user_input: str, db: AsyncSession, kwargs: Dict[str, Any]) -> tuple[Any, IntentResult]:
        """
        进行意图分析并返回目标执行器 (Executor) 以及意图结果。
        """
        intent = await self._resolve_intent(user_input, kwargs)
        intent_key = intent.intent.value if isinstance(intent.intent, Enum) else str(intent.intent)
        
        # 灰度发布开关：根据参数或配置决定是否使用新架构
        use_new_architecture = kwargs.get("use_new_architecture", True)
        
        if use_new_architecture:
            logger.info(f"Routing request based on intent (V2 Architecture): {intent_key}")
            
            # 初始化共享组件
            from app.services.eah_agent.core.components import (
                DefaultMemoryManager,
                DefaultStateManager,
                DefaultPlanValidator,
                DefaultExperienceStore,
                DefaultToolRegistry
            )
            
            memory_manager = DefaultMemoryManager(db=db, llm_model=self.llm_model)
            state_manager = DefaultStateManager(db=db)
            plan_validator = DefaultPlanValidator()
            experience_store = DefaultExperienceStore(db=db)
            tool_registry = DefaultToolRegistry()
    
            # 根据意图进行分发
            if intent_key in ("chat", "data_query", "kg_qa"):
                from app.services.eah_agent.core.executors.fast_executor import FastExecutor
                executor = FastExecutor(llm_model=self.llm_model, memory_manager=memory_manager)
                
            elif intent_key == "task":
                from app.services.eah_agent.core.executors.single_executor import SingleExecutor
                executor = SingleExecutor(
                    llm_model=self.llm_model, 
                    memory_manager=memory_manager,
                    state_manager=state_manager,
                    plan_validator=plan_validator,
                    experience_store=experience_store,
                    tool_registry=tool_registry
                )
                
            elif intent_key == "team":
                from app.services.eah_agent.core.executors.team_executor import TeamExecutor
                executor = TeamExecutor(
                    llm_model=self.llm_model, 
                    memory_manager=memory_manager,
                    state_manager=state_manager,
                    plan_validator=plan_validator,
                    experience_store=experience_store,
                    tool_registry=tool_registry
                )
                
            elif intent_key == "workflow":
                from app.services.eah_agent.core.executors.workflow_executor import WorkflowExecutor
                executor = WorkflowExecutor(
                    llm_model=self.llm_model, 
                    memory_manager=memory_manager,
                    state_manager=state_manager,
                    plan_validator=plan_validator,
                    experience_store=experience_store,
                    tool_registry=tool_registry
                )
                
            else:
                logger.warning(f"Unknown intent {intent_key}, falling back to FastExecutor")
                from app.services.eah_agent.core.executors.fast_executor import FastExecutor
                executor = FastExecutor(llm_model=self.llm_model, memory_manager=memory_manager)
            
            return executor, intent
        else:
            raise ValueError("V1 Architecture has been completely removed. Please set use_new_architecture=True.")

    async def _resolve_intent(self, user_input: str, kwargs: Dict[str, Any]) -> IntentResult:
        """解析用户意图"""
        import asyncio
        
        forced = self._get_forced_intent(kwargs)
        if forced:
            return IntentResult(intent=forced, confidence=1.0, reasoning="Forced intent override.", parameters={})

        try:
            nlu_service = NluService(self.llm_model)
            return await asyncio.wait_for(nlu_service.analyze(user_input), timeout=6.0)
        except Exception as e:
            logger.warning(f"NLU failed or timed out: {e}. Falling back to chat (Fast track).")
            return IntentResult(
                intent="chat",
                confidence=0.0,
                reasoning=f"Router fallback: {e}",
                parameters={},
            )

    def _get_forced_intent(self, kwargs: Dict) -> Optional[str]:
        mode_map = {
            "quick": "chat", "chat": "chat",
            "plan": "task", "task": "task", "solo": "task",
            "team": "team",
            "flow": "workflow", "workflow": "workflow",
            "data": "data_query", "kg": "kg_qa"
        }
        requested = kwargs.get("mode") or kwargs.get("intent_override")
        if isinstance(requested, str):
            return mode_map.get(requested.lower())
        return None
