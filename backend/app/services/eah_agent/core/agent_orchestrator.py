import logging
from typing import AsyncGenerator, Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class AgentWorkflowEngine:
    """
    统一工作流引擎，处理动态与静态编排工作流
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def start_workflow(
        self,
        session_id: str,
        user_goal: str,
        agent_instance: Any = None,
        media_objects: Optional[List[Any]] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        from app.services.eah_agent.workflows.unified_workflow import UnifiedAgentWorkflow

        images = []
        if media_objects:
            for m in media_objects:
                path = getattr(m, "filepath", None)
                if path:
                    images.append(str(path))

        workflow = UnifiedAgentWorkflow(session_id=session_id, db=self.db, user_goal=user_goal, images=images)
        async for event in workflow.run_stream():
            yield event

    async def execute_from_definition(self, session_id: str, definition: Dict[str, Any], history: Optional[List[Dict[str, Any]]] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        执行静态编排工作流定义
        """
        from app.services.eah_agent.workflows.pipelines.dynamic import DynamicWorkflow
        workflow = DynamicWorkflow(db=self.db, session_id=session_id, config=definition, history=history)
        async for event in workflow.run_stream():
            if isinstance(event, str):
                import json
                try:
                    payload = json.loads(event)
                    if isinstance(payload, dict) and payload.get("step"):
                        yield {"type": "status", "content": f"[{payload.get('step')}] {payload.get('status', '')}"}
                        continue
                except Exception:
                    pass
                yield {"type": "content", "content": event}
            elif isinstance(event, dict) and "type" in event:
                yield event
            else:
                yield {"type": "status", "content": str(event)}