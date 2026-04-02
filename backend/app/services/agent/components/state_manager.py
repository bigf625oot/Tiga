import logging
import json
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.chat import ChatSession

logger = logging.getLogger("eah.components.state")

class DefaultStateManager:
    """
    Why: 直连 DB workflow_state，抛弃内存字典，保障跨进程状态流转的 100% 确定性。
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def load_state(self, session_id: str) -> Dict[str, Any]:
        """Why: 实时 DB 读取，保障分布式强一致性。"""
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
        """Why: 原地 update 原子更新，消除先查后写的竞态条件 (Race Condition)。"""
        stmt = (
            update(ChatSession)
            .where(ChatSession.id == session_id)
            .values(workflow_state=state)
        )
        await self.db.execute(stmt)
        await self.db.flush()  # Why: 状态更新融入外层事务边界，由 Executor 统一 commit 保证全局执行原子性。
        logger.debug(f"Saved state for session {session_id}: {state}")

    async def update_status(self, session_id: str, status: str, details: Optional[Dict[str, Any]] = None) -> None:
        state = await self.load_state(session_id)
        state["status"] = status
        if details:
            state.update(details)
            
        await self.save_state(session_id, state)
        logger.info(f"Session {session_id} transitioned to status: {status}")
