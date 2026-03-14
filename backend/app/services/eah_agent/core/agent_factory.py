"""
Agent Factory
核心功能：
- 根据配置创建 Agno 智能体
- 支持自定义模型、工具和技能
- 集成数据库会话管理
"""
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from agno.agent import Agent
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.eah_agent.domain.config import AgentConfig, TeamConfig
from app.services.llm.factory import ModelFactory
from app.models.llm_model import LLMModel
from app.services.eah_agent.tools.tool_factory import ToolFactory
from app.services.eah_agent.skills.loaders.local import LocalSkills
from app.services.eah_agent.skills.manager import Skills

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
            if llm_model:
                model = ModelFactory.create_model(llm_model)
                # Apply model parameters if provided
                if config.model_params:
                    for key, value in config.model_params.items():
                        if hasattr(model, key):
                            setattr(model, key, value)
            else:
                # Fallback to default or load by config.model_id
                # This part depends on how we want to handle model resolution
                pass

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
                show_tool_calls=True,
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
