import logging
from typing import AsyncGenerator, Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import ValidationError
from app.services.eah_agent.core.schema import PlanValidationError
from app.services.eah_agent.workflows.unified_workflow import UnifiedAgentWorkflow

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
        
        images = []
        if media_objects:
            for m in media_objects:
                path = getattr(m, "filepath", None)
                if path:
                    images.append(str(path))

        # 核心容错降级逻辑：如果在创建执行引擎时抛出 PlanValidationError，则尝试用后备模型重试
        max_retries = 2
        # 可选的降级模型列表
        fallback_models = [None, "gpt-4-turbo"] # None 代表使用默认
        
        for attempt in range(max_retries):
            try:
                current_model = fallback_models[attempt] if attempt < len(fallback_models) else fallback_models[-1]
                
                # UnifiedAgentWorkflow 内可能会调用 planner.create_plan 从而抛出 PlanValidationError
                workflow = UnifiedAgentWorkflow(session_id=session_id, db=self.db, user_goal=user_goal, images=images)
                
                # 如果初始化或规划没有问题，执行实际流
                async for event in workflow.run_stream(planner_model_id=current_model):
                    yield event
                break # 成功执行则跳出重试循环
                
            except PlanValidationError as e:
                logger.error(f"Plan validation failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    yield {"type": "status", "content": f"Plan validation failed. Retrying with fallback model... (Attempt {attempt + 2}/{max_retries})"}
                    continue
                else:
                    yield {"type": "error", "content": f"Failed to generate valid plan after {max_retries} attempts: {str(e)}"}
            except Exception as e:
                logger.exception(f"Workflow execution failed: {e}")
                yield {"type": "error", "content": f"Workflow failed: {str(e)}"}
                break

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