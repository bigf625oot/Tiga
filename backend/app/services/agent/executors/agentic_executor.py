import logging
from typing import Any, AsyncGenerator, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.llm_model import LLMModel
from app.services.agent.schemas.intent import IntentResult

logger = logging.getLogger("eah.core.agentic_executor")

class AgenticExecutor:
    """
    智能体/工作流 宏观执行器 (Agentic Paradigm Executor)
    
    物理本质：带状态的循环图 (Cyclic Graph) 或有向无环图 (DAG) 的执行引擎。
    架构价值：对上层 (Router) 隐藏底层执行拓扑的复杂性。内部根据细分 intent 或 agent_id
    动态实例化并调度具体的子执行器 (Single, Team, Workflow)。
    """
    def __init__(
        self,
        llm_model: Optional[LLMModel] = None,
        memory_manager: Any = None,
        state_manager: Any = None,
        plan_validator: Any = None,
        experience_store: Any = None,
        tool_registry: Any = None
    ):
        self.llm_model = llm_model
        self.memory_manager = memory_manager
        self.state_manager = state_manager
        self.plan_validator = plan_validator
        self.experience_store = experience_store
        self.tool_registry = tool_registry

    async def execute(
        self,
        user_input: str,
        intent: IntentResult,
        db: AsyncSession,
        session_id: str,
        **kwargs: Any
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """代理执行逻辑：根据细分意图 (task/team/workflow) 路由到真实的执行拓扑"""
        
        sub_intent = intent.intent.lower()
        logger.info(f"AgenticExecutor activated. Delegating sub_intent: {sub_intent}")

        # 动态组装具体的拓扑执行器
        if sub_intent == "team":
            from app.services.agent.executors.team_executor import TeamExecutor
            concrete_executor = TeamExecutor(
                llm_model=self.llm_model,
                memory_manager=self.memory_manager,
                state_manager=self.state_manager,
                plan_validator=self.plan_validator,
                experience_store=self.experience_store,
                tool_registry=self.tool_registry
            )
        elif sub_intent == "workflow":
            from app.services.agent.executors.workflow_executor import WorkflowExecutor
            concrete_executor = WorkflowExecutor(
                llm_model=self.llm_model,
                memory_manager=self.memory_manager,
                state_manager=self.state_manager,
                plan_validator=self.plan_validator,
                experience_store=self.experience_store,
                tool_registry=self.tool_registry
            )
        else:
            # 默认的 ReAct 单智能体图 (task)
            from app.services.agent.executors.single_executor import SingleExecutor
            concrete_executor = SingleExecutor(
                llm_model=self.llm_model,
                memory_manager=self.memory_manager,
                state_manager=self.state_manager,
                plan_validator=self.plan_validator,
                experience_store=self.experience_store,
                tool_registry=self.tool_registry
            )

        # 透传流式响应
        stream = concrete_executor.execute(user_input, intent, db=db, session_id=session_id, **kwargs)
        async for chunk in stream:
            yield chunk
