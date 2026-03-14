import logging
from typing import Optional, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from agno.agent import Agent as AgnoAgent

from app.models.agent import Agent as AgentModel
from app.models.llm_model import LLMModel
from app.services.llm.factory import ModelFactory
from app.services.eah_agent.tools import default_tools
from app.services.eah_agent.skills.manager import Skills as FileSkillsManager
from app.services.eah_agent.skills.loaders.local import LocalSkills
from app.core.config import settings

from .prompt import InstructionBuilder

logger = logging.getLogger(__name__)

class AgentBuilder:
    """
    Builder class for constructing AgnoAgent instances.
    Encapsulates database access and tool loading logic.
    """
    
    def __init__(self, db: AsyncSession, agent_id: str):
        self.db = db
        self.agent_id = agent_id
        self.agent_model: Optional[AgentModel] = None
        self.llm_model: Optional[LLMModel] = None
        self.tools: List[Any] = []
        self.instructions: str = ""
        self.instruction_builder: InstructionBuilder = InstructionBuilder()

    def _has_global_api_key(self) -> bool:
        return bool(settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.startswith("sk-"))

    async def _fetch_agent_config(self):
        """Fetch agent configuration from DB."""
        result = await self.db.execute(select(AgentModel).filter(AgentModel.id == self.agent_id))
        self.agent_model = result.scalars().first()
        if not self.agent_model:
            raise ValueError(f"Agent {self.agent_id} not found")
        
        # Initialize instruction builder with base system prompt
        base_prompt = getattr(self.agent_model, "system_prompt", None) or "You are a helpful assistant."
        self.instruction_builder = InstructionBuilder(base_prompt)

    async def _fetch_model_config(self):
        """Fetch and resolve LLM model configuration."""
        model_config = getattr(self.agent_model, "model_config", {}) or {}
        llm_model_id = model_config.get("model_id")

        if llm_model_id:
            # Try to find active model with key
            res = await self.db.execute(
                select(LLMModel).filter(
                    LLMModel.model_id == llm_model_id,
                    LLMModel.is_active == True,
                    LLMModel.api_key != None,
                    LLMModel.api_key != "",
                )
            )
            self.llm_model = res.scalars().first()

            if not self.llm_model:
                # Fallback to model without key
                res = await self.db.execute(
                    select(LLMModel).filter(LLMModel.model_id == llm_model_id, LLMModel.is_active == True)
                )
                self.llm_model = res.scalars().first()

        # Fallback logic
        should_fallback = False
        if not self.llm_model:
            should_fallback = True
        elif not self.llm_model.api_key and not self._has_global_api_key():
            should_fallback = True

        if should_fallback:
            res = await self.db.execute(
                select(LLMModel)
                .filter(LLMModel.is_active == True, LLMModel.api_key != None, LLMModel.api_key != "")
                .order_by(LLMModel.updated_at.desc())
            )
            fallback_model = res.scalars().first()
            
            if fallback_model:
                if self.llm_model:
                    logger.warning(
                        f"Agent requested model {self.llm_model.model_id} which has no key. Falling back to {fallback_model.model_id}."
                    )
                self.llm_model = fallback_model
            else:
                # Last resort: try any active model
                if not self.llm_model:
                    res = await self.db.execute(
                        select(LLMModel).filter(LLMModel.is_active == True).order_by(LLMModel.updated_at.desc())
                    )
                    self.llm_model = res.scalars().first()

        if not self.llm_model:
            raise ValueError("No active LLM model found")

    async def _load_tools(self, session_id: str = None, enable_search: bool = False):
        """Load tools using the centralized loader."""
        # Load standard and configured tools
        self.tools = await default_tools.load_tools(self.agent_model, self.db, session_id, enable_search=enable_search)
        
        # Handle file skills specifically as they might add instructions
        skills_config = getattr(self.agent_model, "skills_config", {}) or {}
        file_skills_config = skills_config.get("file_skills", {})
        
        # NOTE: File Skills are now handled inside default_tools.load_tools
        # However, we still need to extract instructions if the tool was loaded
        
        # Iterate loaded tools to find SkillToolkit and extract instructions
        from app.services.eah_agent.skills.toolkit import SkillToolkit
        for tool in self.tools:
            if isinstance(tool, SkillToolkit):
                sys_prompt_snippet = tool.get_system_prompt_snippet()
                self.instruction_builder.add_file_skills(sys_prompt_snippet)
                break

    def _configure_instructions(self):
        """Configure instructions based on loaded tools and capabilities."""
        tools_config = getattr(self.agent_model, "tools_config", []) or []
        skills_config = getattr(self.agent_model, "skills_config", {}) or {}
        
        # Market Skills
        if isinstance(tools_config, list):
             self.instruction_builder.add_market_skills(tools_config)

        # Capabilities based on loaded tools or config
        
        # OpenClaw
        if settings.OPENCLAW_BASE_URL:
            self.instruction_builder.add_openclaw_capabilities()
            
        # Sandbox
        is_sandbox_enabled = skills_config.get("sandbox", {}).get("enabled")
        if not is_sandbox_enabled and isinstance(tools_config, list):
            for t in tools_config:
                if isinstance(t, str) and t.startswith("sb_"):
                    is_sandbox_enabled = True
                    break
        
        if is_sandbox_enabled:
            self.instruction_builder.add_sandbox_capabilities()
            
        # Knowledge Base
        knowledge_config = getattr(self.agent_model, "knowledge_config", None)
        has_documents = False
        if knowledge_config and isinstance(knowledge_config, dict):
            has_documents = bool(knowledge_config.get("document_ids"))
            
        if (knowledge_config or has_documents):
             self.instruction_builder.add_knowledge_capabilities()

    async def build(self, session_id: str = None, enable_search: bool = True) -> AgnoAgent:
        """
        Build and return the AgnoAgent instance.
        """
        # 1. Load configs
        await self._fetch_agent_config()
        await self._fetch_model_config()
        
        # 2. Load Tools
        await self._load_tools(session_id, enable_search=enable_search)
        
        # 3. Configure Instructions
        self._configure_instructions()
        final_instructions = self.instruction_builder.build()
        
        # 4. Create Model Instance
        model = ModelFactory.create_model(self.llm_model)
        is_reasoning = ModelFactory.should_use_agno_reasoning(self.llm_model)
        
        model_config = getattr(self.agent_model, "model_config", {}) or {}
        show_tool_calls = model_config.get("show_tool_calls", False)
        
        # 5. Create Agent
        agent = AgnoAgent(
            name=self.agent_model.name,
            model=model,
            description=getattr(self.agent_model, "description", None),
            instructions=final_instructions,
            tools=self.tools,
            markdown=True,
            reasoning=is_reasoning,
            # show_tool_calls=show_tool_calls,
            debug_mode=True,
        )
        
        return agent
