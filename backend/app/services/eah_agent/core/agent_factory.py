"""
Agent Factory
核心功能：
- 根据配置创建 Agno 智能体
- 支持自定义模型、工具和技能
- 集成数据库会话管理
"""
import logging
from pathlib import Path
from typing import Optional
from agno.agent import Agent
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.eah_agent.domain.config import AgentConfig, TeamConfig
from app.services.llm.factory import ModelFactory
from app.services.llm.resolver import resolve_chat_llm_model
from app.models.llm_model import LLMModel
from app.services.eah_agent.tools.tool_factory import ToolFactory
from app.services.eah_agent.skills.loaders.local import LocalSkills
from app.services.eah_agent.skills.manager import Skills
from app.core.config import settings

logger = logging.getLogger(__name__)

class AgentFactory:
    """
    Factory class to create Agno Agents based on configuration.
    """
    
    @staticmethod
    async def create_agent(config: AgentConfig, db: Optional[AsyncSession] = None, llm_model: Optional[LLMModel] = None) -> Agent:
        """
        Creates a single Agno Agent from config.
        """
        try:
            # 1. Resolve Model
            model = None
            if not llm_model and db:
                llm_model = await resolve_chat_llm_model(db, model_id=config.model_id)

            if llm_model:
                model = ModelFactory.create_model(llm_model)
                # Apply model parameters if provided
                if config.model_params:
                    for key, value in config.model_params.items():
                        if hasattr(model, key):
                            setattr(model, key, value)
                if config.reasoning and llm_model and (llm_model.provider or "").lower() == "deepseek":
                    if hasattr(model, "extra_body") and getattr(model, "extra_body", None) is None:
                        setattr(model, "extra_body", {"thinking": {"type": "enabled"}})
                    if hasattr(model, "reasoning_effort") and getattr(model, "reasoning_effort", None) is None:
                        setattr(model, "reasoning_effort", "high")
                    if hasattr(model, "verbosity") and getattr(model, "verbosity", None) is None:
                        setattr(model, "verbosity", "high")
            else:
                # Fallback to default model if not provided
                # We construct a default LLMModel to use ModelFactory's logic (which includes role_map)
                
                # Determine provider and key from settings
                provider = "openai"
                api_key = settings.OPENAI_API_KEY
                model_id = "gpt-3.5-turbo"
                
                # Check for DeepSeek config
                if settings.DEEPSEEK_API_KEY:
                    provider = "deepseek"
                    api_key = settings.DEEPSEEK_API_KEY
                    model_id = "deepseek-chat"
                elif not api_key:
                    # If no keys, use dummy
                    api_key = "dummy"

                # Check if specific model config exists in kwargs or other sources?
                # Actually, if the user selected a model in the UI, 'llm_model' argument should NOT be None.
                # If 'llm_model' is None, it means the caller didn't pass a model.
                # For QuickHandler (Miaodong), it might be using default.
                
                # If config object has model_id but we are here (llm_model is None), 
                # we should try to use config.model_id if available.
                if config.model_id:
                    model_id = config.model_id
                    # If model_id implies a provider, we might need to guess it or fetch it from DB.
                    # But here we don't have DB access easily to lookup model_id -> provider.
                    # So we rely on defaults or what's in settings.
                    
                    # Simple heuristic for provider based on model_id
                    if "deepseek" in model_id.lower():
                        provider = "deepseek"
                        api_key = settings.DEEPSEEK_API_KEY or api_key
                    elif "gpt" in model_id.lower():
                        provider = "openai"
                        api_key = settings.OPENAI_API_KEY or api_key
                    elif "claude" in model_id.lower():
                        provider = "anthropic"
                        # api_key = settings.ANTHROPIC_API_KEY # if we had it

                default_llm = LLMModel(
                    model_id=model_id,
                    provider=provider,
                    api_key=api_key,
                )
                # If config has model_id, use it
                model = ModelFactory.create_model(default_llm)
                if config.model_params:
                     for key, value in config.model_params.items():
                        if hasattr(model, key):
                            setattr(model, key, value)
                if config.reasoning and (default_llm.provider or "").lower() == "deepseek":
                    if hasattr(model, "extra_body") and getattr(model, "extra_body", None) is None:
                        setattr(model, "extra_body", {"thinking": {"type": "enabled"}})
                    if hasattr(model, "reasoning_effort") and getattr(model, "reasoning_effort", None) is None:
                        setattr(model, "reasoning_effort", "high")
                    if hasattr(model, "verbosity") and getattr(model, "verbosity", None) is None:
                        setattr(model, "verbosity", "high")

            # 2. Load Tools
            tools = []
            # Initialize ToolFactory once
            ToolFactory.initialize()
            
            for tool_cfg in config.tools:
                if tool_cfg.enabled:
                    tool_instance = ToolFactory.create_tool(tool_cfg.name, tool_cfg.config)
                    if tool_instance:
                        tools.append(tool_instance)
                    else:
                        logger.warning(f"Skipping tool '{tool_cfg.name}' for agent '{config.name}' due to creation failure.")

            # 3. Load Skills
            if config.skills:
                try:
                    # Assuming skills directory is at backend/app/services/eah_agent/skills
                    # We need to find the absolute path. Current file is in core/
                    skills_path = Path(__file__).parent.parent / "skills"
                    if skills_path.exists():
                        # We load all skills from the directory
                        # TODO: Filter skills based on config.skills list if needed
                        loader = LocalSkills(str(skills_path), validate=False)
                        skills_manager = Skills([loader])
                        
                        # Get tools and prompt
                        skill_tools = skills_manager.get_tools()
                        tools.extend(skill_tools)
                        
                        skill_prompt = skills_manager.get_system_prompt_snippet()
                        if skill_prompt:
                            config.instructions.append(skill_prompt)
                    else:
                        logger.warning(f"Skills directory not found at {skills_path}")
                except Exception as e:
                    logger.error(f"Failed to load skills: {e}")

            # 4. Create Agent
            agent = Agent(
                model=model,
                description=config.role,
                instructions=config.instructions,
                tools=tools,
                # show_tool_calls=True,  # 中文注释：是否展示工具调用，已被弃用或不支持
                markdown=True,
                reasoning=config.reasoning
            )
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create agent {config.name}: {e}")
            raise e

    @staticmethod
    async def create_team(config: TeamConfig, db: Optional[AsyncSession] = None) -> Agent:
        """
        Creates a Team Agent based on TeamConfig.
        """
        try:
            # 1. Create Member Agents
            members = []
            for member_config in config.members:
                # Create member agent
                member_agent = await AgentFactory.create_agent(member_config, db=db)
                members.append(member_agent)

            # 2. Create Leader Agent
            leader_agent = await AgentFactory.create_agent(config.leader_agent, db=db)
            
            # 3. Assign Team
            # Inject team members into the leader agent
            leader_agent.team = members
            
            # 4. Update Instructions for Coordination
            member_desc = "\n".join([f"- {m.name}: {m.description}" for m in members])
            coordination_prompt = f"\n\n## Team Structure\nYou are the leader of a team consisting of:\n{member_desc}\n\nCoordinate these members to answer the user's request."
            
            # Ensure instructions is a list
            if isinstance(leader_agent.instructions, list):
                leader_agent.instructions.append(coordination_prompt)
            elif isinstance(leader_agent.instructions, str):
                leader_agent.instructions += coordination_prompt
            
            return leader_agent

        except Exception as e:
            logger.error(f"Failed to create team {config.name}: {e}")
            raise e
