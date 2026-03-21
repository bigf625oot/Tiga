"""
Flow Handler:
Handles 'workflow' intent: Defined process execution.
核心功能：
1. 解析用户定义的工作流程（如报告生成、数据处理等）。
2. 执行工作流程中的每个步骤，支持异步操作。
3. 提供执行状态反馈（如“正在执行步骤 1”等）。
4. 处理异常情况，确保工作流程的稳定性。
"""
import logging
import json
import uuid
from typing import AsyncGenerator, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.eah_agent.core.agent_base_handler import BaseHandler, StreamResponse
from app.services.eah_agent.core.agent_nlu import IntentResult
from app.services.eah_agent.workflows.unified_workflow import UnifiedAgentWorkflow
from app.services.eah_agent.workflows.pipelines.dynamic import DynamicWorkflow
from app.services.eah_agent.core.agent_orchestrator import AgentWorkflowEngine
from app.core.i18n import _
from app.models.llm_model import LLMModel
from app.models.workflow import Workflow

logger = logging.getLogger(__name__)

class FlowHandler(BaseHandler):
    """
    Handles 'workflow' intent: Defined process execution.
    """
    
    def __init__(self, llm_model: Optional[LLMModel] = None):
        super().__init__(llm_model)

    async def _load_workflow(self, db: AsyncSession, intent: IntentResult, kwargs: Dict[str, Any]) -> Optional[Workflow]:
        task_params = getattr(intent, "task_params", None) or {}
        params = kwargs.get("params") or {}

        workflow_id = task_params.get("workflow_id") or params.get("workflow_id") or kwargs.get("workflow_id")
        original_id = task_params.get("original_id") or params.get("original_id") or kwargs.get("original_id")
        workflow_name = task_params.get("workflow_name") or params.get("workflow_name") or kwargs.get("workflow_name")
        version = task_params.get("version") or params.get("version") or kwargs.get("version")
        allow_draft = bool(task_params.get("allow_draft") or params.get("allow_draft") or kwargs.get("allow_draft"))

        stmt = None
        if workflow_id:
            stmt = select(Workflow).where(Workflow.id == str(workflow_id))
        elif original_id:
            stmt = select(Workflow).where(Workflow.original_id == str(original_id))
            if version is not None:
                stmt = stmt.where(Workflow.version == int(version))
            else:
                stmt = stmt.where(Workflow.is_latest.is_(True))
        elif workflow_name:
            stmt = select(Workflow).where(Workflow.name == str(workflow_name), Workflow.is_latest.is_(True))

        if stmt is None:
            return None

        if not allow_draft:
            stmt = stmt.where(Workflow.is_draft.is_(False))

        result = await db.execute(stmt)
        return result.scalars().first()

    async def _stream_dynamic_workflow(
        self, db: AsyncSession, session_id: str, definition: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        workflow = DynamicWorkflow(db=db, session_id=session_id, config=definition)
        async for event in workflow.run_stream():
            if isinstance(event, str):
                try:
                    payload = json.loads(event)
                except Exception:
                    yield {"type": "content", "content": event}
                    continue

                if isinstance(payload, dict) and payload.get("step") and payload.get("status"):
                    step = str(payload.get("step"))
                    status = str(payload.get("status"))
                    output = payload.get("output")
                    output_text = "" if output is None else str(output)

                    if status in {"failed", "error"}:
                        yield {"type": "error", "content": f"[{step}] {output_text}".strip()}
                        continue

                    if status == "processing" and output_text:
                        yield {"type": "content", "content": output_text}
                        continue

                    if status == "completed":
                        if output_text:
                            yield {"type": "content", "content": output_text}
                        yield {"type": "status", "content": f"[{step}] completed"}
                        continue

                    yield {"type": "status", "content": f"[{step}] {output_text or status}".strip()}
                    continue

                yield {"type": "content", "content": event}
                continue

            if isinstance(event, dict) and "type" in event:
                yield event
                continue

            yield {"type": "status", "content": event}

    async def process(
        self, input_text: str, intent: Optional[IntentResult] = None, **kwargs: Any
    ) -> AsyncGenerator[StreamResponse, None]:
        db: Optional[AsyncSession] = kwargs.get("db")
        session_id = kwargs.get("session_id") or str(uuid.uuid4())
        images = kwargs.get("images", [])
        
        if not db:
            yield {"type": "error", "content": _("Database session not provided for workflow execution.")}
            return

        try:
            wf = await self._load_workflow(db, intent, kwargs)
            if wf:
                definition = wf.definition or {}
                if isinstance(definition, dict) and definition.get("nodes"):
                    yield {"type": "status", "content": _("正在执行工作流: {} (v{})").format(wf.name, wf.version)}
                    
                    # 加载历史记录，注入工作流上下文，防止“记忆盲区”
                    history_messages, _was_compressed = await self._get_history_messages_with_graph(db, session_id, current_query=input_text)
                    
                    # 替换旧的 DynamicWorkflow，使用统一引擎的静态编排解析
                    engine = AgentWorkflowEngine(db=db)
                    async for chunk in engine.execute_from_definition(session_id, definition, history=history_messages):
                        yield chunk
                    return

                yield {"type": "error", "content": _("工作流定义为空或不支持执行。")}
                return

            # 如果没有找到指定的工作流，自动降级为基于 PlanHandler 的动态规划
            logger.info("No static workflow config found, falling back to dynamic planning (PlanHandler).")
            from app.services.eah_agent.handlers.plan_handler import PlanHandler
            fallback_handler = PlanHandler(self.llm_model)
            # 移除明确传递的参数以防止 kwargs 中重复
            safe_kwargs = {k: v for k, v in kwargs.items() if k not in ("db", "session_id")}
            async for chunk in fallback_handler.process(input_text, intent, db=db, session_id=session_id, **safe_kwargs):
                yield chunk
            
        except Exception as e:
            logger.error(f"FlowHandler processing failed: {e}", exc_info=True)
            yield {"type": "error", "content": f"Workflow execution failed: {e}"}
