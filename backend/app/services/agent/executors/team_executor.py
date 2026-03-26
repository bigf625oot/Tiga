import logging
from typing import AsyncGenerator, Dict, Any, Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from agno.agent import Agent

from app.models.llm_model import LLMModel
from app.services.agent.schemas.intent import IntentResult
from app.services.agent.executors.base.base_executor import BaseExecutor
from app.services.agent.components.memory_manager import DefaultMemoryManager
from app.services.agent.utils.stream_adapter import AgnoStreamAdapter
from app.services.agent.document.file_orchestrator import FileOrchestrator
from app.services.agent.orchestration.factory import AgentFactory
from app.services.agent.domain.config import AgentConfig, TeamConfig, ToolConfig, LLMSettings
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
    [Orchestration] 多智能体协作执行器
    Trade-offs: 基于动态角色分配(Leader-Worker)的微服务架构。提升了复杂域解决能力，但引入了 Agent 间通信开销与不可预测的耗时。
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

        # 1. [Topology Init] 动态构建协作网络
        await self._ensure_team_initialized(db, intent)
        if not self.team_agent:
            yield {"type": "error", "content": "Team initialization failed."}
            return

        # 2. [Context Injection] 上下文感知与边界约束
        input_text = self._enrich_input_with_intent(input_text, intent)
        
        images = []
        if files:
            yield {"type": "status", "content": _("Processing uploaded files for team context...")}
            file_results = await FileOrchestrator.process_batch(files, session_id=session_id)
            if file_results.get("context"):
                input_text += f"\n\n[Uploaded Files Context]\n{file_results['context']}"
            images.extend(file_results.get("media", []))

        # 3. [Memory Bound] 获取并压缩历史记忆
        history_msgs = []
        if self.memory_manager:
            history_msgs = await self.memory_manager.get_compressed_context(session_id, current_query=input_text)

        # 4. [Execution Stream] 协作执行与流式事件适配
        yield {"type": "status", "content": _("Team collaborating...")}
        try:
            run_kwargs = {"messages": history_msgs, "stream": True, "yield_run_output": True}
            if images:
                run_kwargs["images"] = images

            async for chunk in self.team_agent.arun(input_text, **run_kwargs):
                # 适配多智能体协议(如 agent_switch)至标准网关事件
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
            
            # [Sandbox Mount] 代码隔离执行环境挂载
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
        if "entities" in params:
            notes.append(f"Entities: {params['entities']}")
        if "locations" in params:
            notes.append(f"Locations: {params['locations']}")
        
        if notes:
            return f"{input_text}\n\n[Detected Context]: " + " | ".join(notes)
        return input_text
