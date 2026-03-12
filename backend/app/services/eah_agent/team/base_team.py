"""
定义 Team 的公共配置、共享存储等
"""

from typing import List, Optional, Any, Dict
from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession
from agno.agent import Agent as AgnoAgent
from app.services.eah_agent.agent.builder import AgentBuilder

class BaseTeam(ABC):
    """
    Base class for Agno Teams.
    Provides functionality to build member agents from configuration.
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        self.team_agent: Optional[AgnoAgent] = None
        self.members: List[AgnoAgent] = []

    async def _build_member_agent(self, agent_id: str) -> AgnoAgent:
        """
        Build a member agent using the standard AgentBuilder.
        """
        builder = AgentBuilder(self.db, agent_id)
        # Member agents usually don't need independent session history for the team context,
        # but if needed, session_id can be passed.
        # Here we build them as stateless workers initially.
        return await builder.build()

    @abstractmethod
    async def initialize(self, **kwargs) -> AgnoAgent:
        """
        Initialize the team and return the leader agent.
        """
        pass

    async def run(self, message: str) -> Any:
        """
        Run the team with a user message.
        """
        if not self.team_agent:
            raise ValueError("Team not initialized")
        return self.team_agent.print_response(message, stream=True)
