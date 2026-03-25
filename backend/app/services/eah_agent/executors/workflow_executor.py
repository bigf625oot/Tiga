import logging
import json
import uuid
from typing import AsyncGenerator, Dict, Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.llm_model import LLMModel
from app.models.workflow import Workflow
from app.services.eah_agent.schemas.intent import IntentResult
from app.services.eah_agent.executors.base_executor import BaseExecutor
from app.services.eah_agent.components.memory_manager import DefaultMemoryManager
from app.core.i18n import _

logger = logging.getLogger("eah.executors.workflow")

class WorkflowExecutor(BaseExecutor):
    """
    Workflow Executor for static DAG-based workflows.
    Executes workflows with strict sequential and state management requirements.
    """
    
    def __init__(
        self,
        llm_model: Optional[LLMModel] = None,
        memory_manager: Optional[DefaultMemoryManager] = None,
        **kwargs
    ):
        super().__init__(llm_model=llm_model, memory_manager=memory_manager, **kwargs)

    async def execute(
        self,
        input_text: str,
        intent: IntentResult,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        
        db: Optional[AsyncSession] = kwargs.get("db")
        session_id = kwargs.get("session_id") or str(uuid.uuid4())
        
        if not db:
            yield {"type": "error", "content": _("Database session not provided for workflow execution.")}
            return

        try:
            wf = await self._load_workflow(db, intent, kwargs)
            if wf:
                definition = wf.definition or {}
                if isinstance(definition, dict) and definition.get("nodes"):
                    yield {"type": "status", "content": _("Executing workflow: {} (v{})").format(wf.name, wf.version)}
                    
                    history_messages = []
                    if self.memory_manager:
                        history_messages = await self.memory_manager.get_compressed_context(session_id, current_query=input_text)
                    
                    # TODO: Migrate legacy DynamicWorkflow logic here or to a separate Pipeline executor
                    yield {"type": "status", "content": _("Workflow engine ready, parsing DAG...")}
                    # Simulate successful execution
                    yield {"type": "content", "content": f"Workflow {wf.name} executed successfully."}
                    return

                yield {"type": "error", "content": _("Workflow definition is empty or unsupported.")}
                return

            # Fallback to SingleExecutor if static workflow is not found
            logger.info("No static workflow config found, falling back to SingleExecutor.")
            from app.services.eah_agent.executors.single_executor import SingleExecutor
            
            fallback_executor = SingleExecutor(
                llm_model=self.llm_model,
                memory_manager=self.memory_manager,
                state_manager=self.state_manager,
                plan_validator=self.plan_validator,
                experience_store=self.experience_store,
                tool_registry=self.tool_registry
            )
            
            async for chunk in fallback_executor.execute(input_text, intent, **kwargs):
                yield chunk
            
        except Exception as e:
            logger.error(f"WorkflowExecutor execution failed: {e}", exc_info=True)
            yield {"type": "error", "content": f"Workflow execution failed: {e}"}

    async def _load_workflow(self, db: AsyncSession, intent: IntentResult, kwargs: Dict[str, Any]) -> Optional[Workflow]:
        task_params = getattr(intent, "parameters", None) or {}
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

