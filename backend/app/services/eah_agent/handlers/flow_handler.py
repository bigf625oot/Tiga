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
import uuid
from typing import AsyncGenerator, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.eah_agent.core.base_handler import BaseHandler
from app.services.eah_agent.core.nlu import IntentResult
from app.services.eah_agent.core.workflow import AgentWorkflowEngine
from app.core.i18n import _
from app.models.llm_model import LLMModel

logger = logging.getLogger(__name__)

class FlowHandler(BaseHandler):
    """
    Handles 'workflow' intent: Defined process execution.
    """
    
    def __init__(self, llm_model: Optional[LLMModel] = None):
        super().__init__(llm_model)

    async def process(self, input_text: str, intent: IntentResult, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        db: Optional[AsyncSession] = kwargs.get("db")
        session_id = kwargs.get("session_id") or str(uuid.uuid4())
        
        if not db:
             yield {"type": "error", "content": _("Database session not provided for workflow execution.")}
             return

        try:
            yield {"type": "status", "content": _("Initializing Workflow Engine...")}
            
            # Initialize Workflow Engine
            engine = AgentWorkflowEngine(db)
            
            # Start workflow and stream events
            # We treat input_text as the user_goal for now
            async for event in engine.start_workflow(session_id, input_text):
                yield event
            
        except Exception as e:
            logger.error(f"FlowHandler processing failed: {e}")
            yield {"type": "error", "content": _("Workflow execution failed.")}
