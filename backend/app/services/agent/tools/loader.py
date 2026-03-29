from typing import List, Any, Type, Union
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from agno.tools import Toolkit

from app.services.agent.capabilities import (
    CapabilityRegistry,
    LocalCapabilityProvider,
    SkillCapabilityProvider,
    MCPCapabilityProvider,
    KnowledgeCapabilityProvider,
    OpenClawCapabilityProvider
)

logger = logging.getLogger(__name__)

class ToolsManager:
    """
    P10 Refactored: Manager for loading and configuring agent tools using CapabilityRegistry.
    """
    
    def __init__(self):
        self._custom_tools: List[Union[Toolkit, Type[Toolkit]]] = []
        
    def add_tool(self, tool: Union[Toolkit, Type[Toolkit]]):
        """
        Add a custom tool to the registry.
        """
        self._custom_tools.append(tool)
        
    async def load_tools(self, agent_model: Any, db: AsyncSession = None, session_id: str = None, enable_search: bool = False, suggested_tools: List[str] = None) -> List[Any]:
        """
        Load tools progressively based on NLU suggestions instead of eager loading all.
        """
        registry = CapabilityRegistry()
        
        tools_config = getattr(agent_model, "tools_config", []) or []
        skills_config = getattr(agent_model, "skills_config", {}) or {}
        mcp_config = getattr(agent_model, "mcp_config", []) or []
        knowledge_config = getattr(agent_model, "knowledge_config", None)
        
        # 如果 NLU 有推荐工具，覆盖 agent_model 的 tools_config 以实现按需挂载
        # 否则回退到 agent_model 预设的配置（防御性降级）
        if suggested_tools is not None and len(suggested_tools) > 0:
            tools_config = [{"name": t} for t in suggested_tools]
            logger.info(f"Progressive loading active: replacing tools_config with {suggested_tools}")

        # 1. Local Tools Provider
        registry.register_provider(LocalCapabilityProvider(
            tools_config=tools_config,
            enable_search=enable_search,
            session_id=session_id
        ))
        
        # 2. Skills Provider
        registry.register_provider(SkillCapabilityProvider(
            skills_config=skills_config,
            tools_config=tools_config,
            db=db
        ))
        
        # 3. MCP Provider
        registry.register_provider(MCPCapabilityProvider(
            mcp_configs=mcp_config,
            agent_id=agent_model.id
        ))
        
        # 4. Knowledge Provider
        registry.register_provider(KnowledgeCapabilityProvider(
            knowledge_config=knowledge_config
        ))
        
        # 5. OpenClaw Provider
        registry.register_provider(OpenClawCapabilityProvider())
        
        # Resolve all tools concurrently (Performance P10)
        tools = await registry.resolve_all_tools()
        
        # Add legacy custom tools
        for custom_tool in self._custom_tools:
            try:
                if isinstance(custom_tool, type):
                    tools.append(custom_tool())
                else:
                    tools.append(custom_tool)
            except Exception as e:
                logger.error(f"Failed to load custom tool {custom_tool}: {e}")

        return tools

default_tools = ToolsManager()
