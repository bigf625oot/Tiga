import logging
import asyncio
from typing import AsyncGenerator, Dict, Any, Optional, List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from agno.agent import Agent

from app.models.llm_model import LLMModel
from app.services.eah_agent.schemas.intent import IntentResult
from app.services.eah_agent.executors.base_executor import BaseExecutor
from app.services.eah_agent.components.memory_manager import DefaultMemoryManager
from app.services.eah_agent.utils.stream_adapter import AgnoStreamAdapter
from app.services.eah_agent.document.file_orchestrator import FileOrchestrator
from app.services.eah_agent.orchestration.factory import AgentFactory
from app.services.eah_agent.domain.config import AgentConfig, TeamConfig, ToolConfig, LLMSettings
from app.core.config import settings
from app.core.i18n import _

logger = logging.getLogger("eah.executors.team")

try:
    from agno.tools.e2b import E2BTools
    HAS_E2B = True
except ImportError:
    HAS_E2B = False

class TeamExecutor(BaseExecutor):
    """
    Team Executor.
    """

    def __init__(
        self,
        llm_model: Optional[LLMModel] = None,
        memory_manager: Optional[DefaultMemoryManager] = None,
        **kwargs
    ):
        super().__init__(llm_model=llm_model, memory_manager=memory_manager, **kwargs)
        self.team_agent: Optional[Agent] = None
        self.stream_adapter = AgnoStreamAdapter()

    async def execute(
        self,
        input_text: str,
        intent: IntentResult,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        
        db: AsyncSession = kwargs.get("db")
        session_id: str = kwargs.get("session_id")
        files: List[Any] = kwargs.get("files", [])

        # 1. 团队初始化
        await self._ensure_team_initialized(db, intent)
        if not self.team_agent:
            yield {"type": "error", "content": "Team initialization failed."}
            return

        # 2. 上下文准备
        input_text = self._enrich_input_with_intent(input_text, intent)
        
        images = []
        if files:
            yield {"type": "status", "content": _("Processing uploaded files for team context...")}
            file_results = await FileOrchestrator.process_batch(files, session_id=session_id)
            if file_results.get("context"):
                input_text += f"\n\n[Uploaded Files Context]\n{file_results['context']}"
            images.extend(file_results.get("media", []))

        # 3. 获取历史记忆
        history_msgs = []
        if self.memory_manager:
            history_msgs = await self.memory_manager.get_compressed_context(session_id, current_query=input_text)

        # 4. 执行流
        yield {"type": "status", "content": _("Team collaborating...")}
        try:
            run_kwargs = {"messages": history_msgs, "stream": True, "yield_run_output": True}
            if images:
                run_kwargs["images"] = images

            async for chunk in self.team_agent.arun(input_text, **run_kwargs):
                # 利用 AgnoStreamAdapter 处理复杂的多智能体流式事件 (如 agent_switch)
                async for event in self.stream_adapter.to_standard_events(chunk):
                    yield event
                    
            async for event in self.stream_adapter.flush():
                yield event

        except Exception as e:
            logger.error(f"TeamExecutor execution failed: {e}", exc_info=True)
            yield self._yield_error(_("Team execution encountered a failure"), e)

    async def _ensure_team_initialized(self, db: AsyncSession, intent: IntentResult):
        if self.team_agent:
            return

        try:
            members = []
            task_params = intent.parameters if intent else {}
            
            team_type = task_params.get("team_type", "dynamic")
            roles = task_params.get("roles", [])
            
            if team_type == "research" or "researcher" in roles:
                members.append(AgentConfig(
                    name="Researcher",
                    role="Research Specialist",
                    instructions=["Search for information.", "Verify facts."],
                    tools=[ToolConfig(name="duckduckgo", enabled=True)], 
                    llm=LLMSettings(reasoning=True, temperature=0.3)
                ))

            if team_type == "coding" or "developer" in roles:
                if HAS_E2B and settings.E2B_API_KEY:
                    members.append(AgentConfig(
                        name="Developer",
                        role="Senior Developer",
                        instructions=["Write and execute code in E2B sandbox."],
                        tools=[],
                        llm=LLMSettings(reasoning=True, temperature=0.1)
                    ))
            
            members.append(AgentConfig(
                name="Writer",
                role="Content Writer",
                instructions=["Write engaging content based on research/code."],
                tools=[],
                llm=LLMSettings(reasoning=False, temperature=0.7)
            ))
            
            leader_config = AgentConfig(
                name="TeamLeader",
                role="Team Coordinator",
                instructions=[
                    "Coordinate team members to answer the request.",
                    "Break down complex tasks and assign them."
                ],
                tools=[],
                llm=LLMSettings(reasoning=True, temperature=0.1)
            )
            
            team_config = TeamConfig(
                team_id="dynamic_team",
                name="DynamicTeam",
                leader=leader_config,
                members=members
            )
            
            self.team_agent = await AgentFactory.create_team(team_config, llm_model=self.llm_model)
            
            # E2B 挂载
            if self.team_agent and self.team_agent.team:
                for member in self.team_agent.team:
                    if member.name == "Developer" and HAS_E2B and settings.E2B_API_KEY:
                        member.tools.append(E2BTools(api_key=settings.E2B_API_KEY))

        except Exception as e:
            logger.error(f"Failed to create team agent: {e}")

    def _enrich_input_with_intent(self, input_text: str, intent: IntentResult) -> str:
        if not intent or not intent.parameters:
            return input_text
            
        params = intent.parameters
        notes = []
        if "entities" in params: notes.append(f"Entities: {params['entities']}")
        if "locations" in params: notes.append(f"Locations: {params['locations']}")
        
        if notes:
            return f"{input_text}\n\n[Detected Context]: " + " | ".join(notes)
        return input_text
