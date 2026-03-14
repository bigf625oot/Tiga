"""
Team Handler:
Handles 'team' intent: Multi-agent collaboration.
核心功能：
1. 协调多个智能体（如研究代理、数据代理等）合作完成任务。
2. 支持异步操作，确保在高并发场景下的响应速度。
3. 提供基础的错误处理机制，避免系统崩溃。
"""
import logging
from typing import AsyncGenerator, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.eah_agent.core.base_handler import BaseHandler
from app.services.eah_agent.core.nlu import IntentResult
from app.services.eah_agent.core.agent_factory import AgentFactory
from app.services.eah_agent.domain.config import AgentConfig, TeamConfig
from app.core.i18n import _
from app.models.llm_model import LLMModel
from agno.agent import Agent

logger = logging.getLogger(__name__)

class TeamHandler(BaseHandler):
    """
    Handles 'team' intent: Multi-agent collaboration.
    """
    
    def __init__(self, llm_model: Optional[LLMModel] = None):
        super().__init__(llm_model)
        self.team_agent: Optional[Agent] = None

    async def _ensure_team_initialized(self, db: Optional[AsyncSession] = None):
        if not self.team_agent and self.llm_model:
            try:
                # 创建默认团队配置
                # In a real scenario, this would come from NLU parameters or DB
                # TODO: Implement dynamic team configuration based on intent
                
                # Example: Research Team
                researcher_config = AgentConfig(
                    name="Researcher",
                    role="Research Specialist",
                    instructions=["Search for information.", "Verify facts."],
                    tools=[], # Should include search tools
                    skills=[],
                    reasoning=True,
                    model_params={"temperature": 0.3}
                )
                
                writer_config = AgentConfig(
                    name="Writer",
                    role="Content Writer",
                    instructions=["Write engaging content based on research.", "Format with Markdown."],
                    tools=[],
                    skills=[],
                    reasoning=False,
                    model_params={"temperature": 0.7}
                )
                
                leader_config = AgentConfig(
                    name="TeamLeader",
                    role="Team Coordinator",
                    instructions=["Coordinate the team.", "Review outputs."],
                    tools=[],
                    skills=[],
                    reasoning=True,
                    model_params={"temperature": 0.1}
                )
                
                team_config = TeamConfig(
                    name="ResearchTeam",
                    leader_agent=leader_config,
                    members=[researcher_config, writer_config]
                )
                
                self.team_agent = await AgentFactory.create_team(team_config, db=db)
                
            except Exception as e:
                logger.error(f"Failed to create team agent: {e}")
                self.team_agent = None

    async def process(self, input_text: str, intent: IntentResult, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        db = kwargs.get("db")
        await self._ensure_team_initialized(db)
        
        if not self.team_agent:
             yield {"type": "error", "content": _("Team initialization failed.")}
             return

        try:
            yield {"type": "status", "content": _("Team collaborating...")}
            
            # Execute the team agent with streaming
            # Assuming agent.run(stream=True) returns a generator
            response_stream = self.team_agent.run(input_text, stream=True)
            
            for chunk in response_stream:
                # Extract content from the chunk
                content = getattr(chunk, 'content', None)
                
                if content:
                     yield {"type": "content", "content": content}
                elif isinstance(chunk, str):
                     yield {"type": "content", "content": chunk}
            
        except Exception as e:
            logger.error(f"TeamHandler processing failed: {e}")
            yield {"type": "error", "content": _("Team execution failed.")}
