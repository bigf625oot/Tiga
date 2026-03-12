"""
工作流专用的辅助函数（如状态持久化、格式转换）
"""

import json
import logging

from typing import Any, Optional
from app.services.eah_agent.workflow.base import EAHWorkflowState

logger = logging.getLogger(__name__)

async def persist_workflow_state(session_id: str, state: EAHWorkflowState):
    """持久化工作流状态到数据库或缓存"""
    logger.info(f"Persisting state for session {session_id}, step: {state.current_step}")
    # TODO: 实现具体的 DB 写入逻辑
    # e.g., await db.execute(update(WorkflowSession).where(...).values(state=state.model_dump()))
    pass

def format_workflow_event(step: str, status: str, output: str = None, **kwargs) -> str:
    """格式化为 SSE 流式输出的 JSON 字符串"""
    event = {"step": step, "status": status, "output": output}
    event.update(kwargs)
    return json.dumps(event)
