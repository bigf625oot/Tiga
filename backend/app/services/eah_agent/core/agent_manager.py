import logging
import inspect
from typing import Optional, List, Any, TYPE_CHECKING

from agno.agent import Agent as AgnoAgent
# from agno.tools.duckduckgo import DuckDuckGoTools # Removed: Handled by loader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from app.services.eah_agent.core.planner import PlannerAgent
    from app.services.eah_agent.core.executor import ExecutorAgent

# from agno.tools.python import PythonTools # Assuming this exists or similar
from app.models.agent import Agent as AgentModel
from app.models.chat import ChatMessage
from app.models.llm_model import LLMModel
from app.services.rag.knowledge_base import kb_service
from app.services.eah_agent.skills.manager import Skills as FileSkillsManager
from app.services.eah_agent.skills.loaders.local import LocalSkills

logger = logging.getLogger(__name__)

from app.core.config import settings
from app.services.llm.factory import ModelFactory
# from app.services.eah_agent.tools.registry import discover_tools # Removed: Handled by loader

try:
    from app.services.mcp.client import mcp_pool
except Exception:
    mcp_pool = None


def has_global_api_key():
    return bool(settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.startswith("sk-"))


class AgentManager:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def create_agno_agent(self, db: AsyncSession, agent_id: str, session_id: str = None, enable_search: bool = True) -> AgnoAgent:
        """
        Creates an AgnoAgent instance using the unified AgentBuilder.
        """
        try:
            from app.services.eah_agent.agent.builder import AgentBuilder
            builder = AgentBuilder(db, agent_id)
            return await builder.build(session_id, enable_search)
        except Exception as e:
            logger.exception(f"Error creating agent {agent_id}")
            raise e

    async def create_team(self, db: AsyncSession, team_type: str, config: dict) -> AgnoAgent:
        """
        Creates a specialized team agent.
        """
        try:
            if team_type == "research":
                from app.services.eah_agent.team.research_team import ResearchTeam
                team = ResearchTeam(db)
                return await team.initialize(**config)
            elif team_type == "operations":
                from app.services.eah_agent.team.operations_team import OperationsTeam
                team = OperationsTeam(db)
                return await team.initialize(**config)
            elif team_type == "dynamic":
                from app.services.eah_agent.team.dynamic_team import DynamicTeam
                team = DynamicTeam(db)
                return await team.initialize(**config)
            else:
                raise ValueError(f"Unknown team type: {team_type}")
        except Exception as e:
            logger.exception(f"Error creating team {team_type}")
            raise e

    async def get_planner_agent(self, db: AsyncSession, model_id: str = "gpt-4-turbo") -> 'PlannerAgent':
        from app.services.eah_agent.core.planner import PlannerAgent
        return PlannerAgent(self, db, model_id)

    async def get_executor_agent(self, db: AsyncSession, agent_id: str = None) -> 'ExecutorAgent':
        from app.services.eah_agent.core.executor import ExecutorAgent
        return ExecutorAgent(self, db)

agent_manager = AgentManager.get_instance()
