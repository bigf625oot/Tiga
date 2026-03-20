from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.eah_agent.core.agent_builder import AgentAssembler as _Builder


class AgentAssembler:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def assemble(
        self,
        agent_id: str,
        session_id: Optional[str] = None,
        enable_search: Optional[bool] = None,
        reasoning_override: Optional[bool] = None,
        **kwargs: Any,
    ):
        builder = _Builder(self.db, agent_id)
        return await builder.build(
            session_id=session_id,
            enable_search=enable_search,
            enable_reasoning=reasoning_override,
            **kwargs,
        )

