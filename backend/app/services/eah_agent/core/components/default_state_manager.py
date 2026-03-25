import logging
import json
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession


logger = logging.getLogger("eah.components.state")

class DefaultStateManager:
    """
    默认的 StateManager 实现。
    目前使用内存字典进行简单的状态存储，未来可对接 Redis 或 PostgreSQL。
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        # 内存存储作为临时方案
        self._states: Dict[str, Dict[str, Any]] = {}

    async def load_state(self, session_id: str) -> Dict[str, Any]:
        """加载指定会话的状态"""
        return self._states.get(session_id, {})

    async def save_state(self, session_id: str, state: Dict[str, Any]) -> None:
        """保存当前会话的状态"""
        self._states[session_id] = state
        logger.debug(f"Saved state for session {session_id}: {state}")

    async def update_status(self, session_id: str, status: str, details: Optional[Dict[str, Any]] = None) -> None:
        """更新当前执行所处的生命周期状态"""
        state = await self.load_state(session_id)
        state["status"] = status
        if details:
            state.update(details)
        await self.save_state(session_id, state)
        logger.info(f"Session {session_id} transitioned to status: {status}")
