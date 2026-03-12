from abc import ABC, abstractmethod
from typing import AsyncGenerator, Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class BaseAgentExecutor(ABC):
    @abstractmethod
    async def execute(self, message: str, **kwargs) -> Any:
        pass

    @abstractmethod
    async def stream(self, message: str, **kwargs) -> AsyncGenerator[str, None]:
        pass

class ChatAgentExecutor(BaseAgentExecutor):
    def __init__(self, session_id: str):
        from app.workflow.app_workflow import AppWorkflow
        self.workflow = AppWorkflow(session_id=session_id, mode="static")

    async def execute(self, message: str, **kwargs) -> Any:
        return await self.workflow.run(message, **kwargs)

    async def stream(self, message: str, **kwargs) -> AsyncGenerator[str, None]:
        async for event in self.workflow.run_stream(message, **kwargs):
            yield event

class WorkflowAgentExecutor(BaseAgentExecutor):
    def __init__(self, session_id: str):
        from app.workflow.app_workflow import AppWorkflow
        self.workflow = AppWorkflow(session_id=session_id, mode="dynamic")

    async def execute(self, message: str, **kwargs) -> Any:
        return await self.workflow.run(message, **kwargs)

    async def stream(self, message: str, **kwargs) -> AsyncGenerator[str, None]:
        async for event in self.workflow.run_stream(message, **kwargs):
            yield event

class AutoTaskAgentExecutor(BaseAgentExecutor):
    def __init__(self, session_id: str):
        # For now, we reuse AppWorkflow with auto_task mode if supported, 
        # or we will implement specific logic later.
        # Assuming AppWorkflow might be extended or we use a different service.
        # But based on current AppWorkflow, it only supports static/dynamic.
        # So we might need to implement this.
        # For now, let's treat it similar to Workflow but maybe with different params?
        from app.workflow.app_workflow import AppWorkflow
        self.workflow = AppWorkflow(session_id=session_id, mode="auto_task")

    async def execute(self, message: str, **kwargs) -> Any:
        # TODO: Implement AutoTask specific sync execution
        return await self.workflow.run(message, **kwargs)

    async def stream(self, message: str, **kwargs) -> AsyncGenerator[str, None]:
        # TODO: Implement AutoTask specific stream execution
        async for event in self.workflow.run_stream(message, **kwargs):
            yield event

def get_executor(mode: str, session_id: str) -> BaseAgentExecutor:
    if mode == "chat" or mode == "static": # "static" is the internal name in AppWorkflow for simple chat
        return ChatAgentExecutor(session_id)
    elif mode == "workflow" or mode == "dynamic": # "dynamic" is internal name for planner
        return WorkflowAgentExecutor(session_id)
    elif mode == "auto_task":
        return AutoTaskAgentExecutor(session_id)
    else:
        # Default to Chat
        logger.warning(f"Unknown mode {mode}, defaulting to ChatAgentExecutor")
        return ChatAgentExecutor(session_id)

class ExecutorAgent:
    """
    Agent responsible for executing specific tasks assigned by the PlannerAgent.
    """
    def __init__(self, agent_manager, db):
        self.agent_manager = agent_manager
        self.db = db
        
    async def run_task(self, task_id: str, context: Optional[Dict] = None):
        """
        Execute a specific task.
        """
        logger.info(f"ExecutorAgent running task {task_id}")
        # Implementation to be added
        pass
