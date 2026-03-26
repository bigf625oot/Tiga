import logging
import json
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.chat import ChatSession

logger = logging.getLogger("eah.components.state")

class DefaultStateManager:
    """
    State Manager: 生产级会话状态管理
    职责：负责维护会话的生命周期状态 (planning -> executing -> reflecting -> completed/failed)
    架构：抛弃单机内存字典，直连数据库 `chat_sessions.workflow_state`，实现跨请求、跨进程的状态流转确定性。
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def load_state(self, session_id: str) -> Dict[str, Any]:
        """
        加载指定会话的状态。
        Why: 每次从数据库实时读取，保证分布式架构下的强一致性。
        """
        stmt = select(ChatSession.workflow_state).where(ChatSession.id == session_id)
        result = await self.db.execute(stmt)
        state_data = result.scalar_one_or_none()
        
        if isinstance(state_data, dict):
            return state_data
        elif isinstance(state_data, str):
            try:
                return json.loads(state_data)
            except json.JSONDecodeError:
                logger.warning(f"Failed to decode workflow_state for session {session_id}")
                return {}
        return {}

    async def save_state(self, session_id: str, state: Dict[str, Any]) -> None:
        """
        保存当前会话的状态。
        Why: 利用 update 语句进行原子更新，避免先查后写的竞态条件 (Race Condition)。
        """
        stmt = (
            update(ChatSession)
            .where(ChatSession.id == session_id)
            .values(workflow_state=state)
        )
        await self.db.execute(stmt)
        await self.db.flush()  # Why flush not commit: state update is part of the enclosing request transaction.
        # The caller (Executor) owns the commit boundary to ensure atomicity across the full plan execution.
        logger.debug(f"Saved state for session {session_id}: {state}")

    async def update_status(self, session_id: str, status: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        更新当前执行所处的生命周期状态。
        """
        state = await self.load_state(session_id)
        state["status"] = status
        if details:
            state.update(details)
            
        await self.save_state(session_id, state)
        logger.info(f"Session {session_id} transitioned to status: {status}")
