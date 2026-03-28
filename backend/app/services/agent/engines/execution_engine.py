import logging
from typing import AsyncGenerator, Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from agno.agent import Agent

from app.models.llm_model import LLMModel
from app.services.platform.llm.factory import ModelFactory
from app.services.agent.schemas.plan import ExecutionTaskStep
from app.services.agent.utils.stream_adapter import AgnoStreamAdapter
from app.services.agent.components.tool_registry import DefaultToolRegistry

logger = logging.getLogger("eah.core.engines.execution")

class ExecutionEngine:
    """
    执行引擎 (Execution Engine)
    负责承接单个 Task 的执行，动态挂载 ToolRegistry 中的工具，
    调用大模型完成实际的工具交互和任务达成，并返回流式结果。
    """
    def __init__(self, db: AsyncSession, tool_registry: DefaultToolRegistry, llm_model: Optional[LLMModel] = None):
        self.db = db
        self.tool_registry = tool_registry
        self.llm_model = llm_model

    async def execute_task(
        self, 
        task: ExecutionTaskStep, 
        context: List[Dict[str, Any]], 
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        执行单个原子任务，产生流式输出。
        """
        logger.info(f"ExecutionEngine starting task: {task.task_id} ({task.title})")
        
        if not self.llm_model:
            from app.services.platform.llm.resolver import resolve_chat_llm_model
            self.llm_model = await resolve_chat_llm_model(self.db)
            
        model_instance = ModelFactory.create_model(self.llm_model)

        # 这里应当根据 task.executor_role 从 ToolRegistry 提取需要的工具
        # 为简化，当前提取 registry 中的所有工具或特定 role 的工具
        tools = self._resolve_tools_for_role(task.executor_role)
        
        system_prompt = (
            f"You are executing a sub-task: '{task.title}'.\n"
            f"Role: {task.executor_role}\n"
            f"Task Description: {task.description}\n"
            f"Expected Output: {task.expected_output}\n"
            "Complete this specific task using the tools provided if necessary."
        )

        agent = Agent(
            name=f"Executor-{task.task_id}",
            model=model_instance,
            tools=tools,
            instructions=[system_prompt],
            markdown=True
        )

        # 转换上下文为字符串或者传递给 agent
        # (实际实现中可能需要将 context 转换给 agent.run)
        context_str = "\n".join([str(c) for c in context]) if context else ""
        prompt = f"Context:\n{context_str}\n\nTask Goal:\n{task.description}\n\nExecute the task directly. Do NOT repeat the plan. Do NOT output meta-commentary."

        adapter = AgnoStreamAdapter()
        raw_stream = agent.arun(prompt, stream=True, stream_events=True)
        
        async for chunk in raw_stream:
            async for event in adapter.to_standard_events(chunk):
                # 注入 task_id 确保前端能将工具调用和日志关联到特定节点
                if hasattr(event, "data") and event.data is None:
                    event.data = {}
                elif getattr(event, "data", None) is None:
                    try:
                        event.data = {}
                    except Exception:
                        pass
                
                # Try to safely attach task_id to the event dict representation
                event_dict = event.to_dict() if hasattr(event, "to_dict") else vars(event)
                if "task_id" not in event_dict:
                    event_dict["task_id"] = task.task_id
                    
                # We need to make sure the yielded event is still a dict or StreamEvent that retains task_id
                if hasattr(event, "to_dict"):
                    # Create a new event or just yield dict
                    yield event_dict
                else:
                    yield event
                
        async for event in adapter.flush():
            event_dict = event.to_dict() if hasattr(event, "to_dict") else vars(event)
            if "task_id" not in event_dict:
                event_dict["task_id"] = task.task_id
            yield event_dict

    def _resolve_tools_for_role(self, role: str) -> List[Any]:
        """
        根据角色从 ToolRegistry 分配专属工具。
        Why: 防止大模型被过多无关工具干扰（Context Window Pollution）。
        """
        return self.tool_registry.build_from_hint(role)
