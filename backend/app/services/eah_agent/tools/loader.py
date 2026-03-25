from typing import List, Any, Type, Union
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from agno.tools import Toolkit

from .libs.duckduckgo import DuckDuckGoTools
from .libs.sandbox_tools import SandboxTools
from .registry import discover_tools
from app.services.eah_agent.utils.secret_refs import resolve_secret_refs

try:
    from app.services.openclaw import OpenClawTools
except ImportError:
    OpenClawTools = None



try:
    from app.services.knowledge.rag.mcp_server import search_knowledge_base, query_knowledge_graph
    HAS_KNOWLEDGE_TOOLS = True
except ImportError:
    HAS_KNOWLEDGE_TOOLS = False

logger = logging.getLogger(__name__)

class ToolsManager:
    """
    Manager for loading and configuring agent tools.
    Follows the pattern: from agno.tools import default_tools
    """
    
    def __init__(self):
        self._custom_tools: List[Union[Toolkit, Type[Toolkit]]] = []
        self._available_tools_map = discover_tools()
        
    def add_tool(self, tool: Union[Toolkit, Type[Toolkit]]):
        """
        Add a custom tool to the registry.
        """
        self._custom_tools.append(tool)
        
    async def load_tools(self, agent_model: Any, db: AsyncSession = None, session_id: str = None, enable_search: bool = False) -> List[Any]:
        """
        Load all tools based on agent configuration and defaults.
        """
        tools = []
        
        tools_config = getattr(agent_model, "tools_config", []) or []
        skills_config = getattr(agent_model, "skills_config", {}) or {}
        mcp_config = getattr(agent_model, "mcp_config", []) or []
        
        loaded_names = set()
        
        if isinstance(tools_config, list):
            for entry in tools_config:
                tool_name = ""
                tool_config = {}
                
                if isinstance(entry, str):
                    tool_name = entry.lower()
                elif isinstance(entry, dict):
                    if entry.get("type") == "skill":
                        continue
                    tool_name = entry.get("name", "").lower()
                    tool_config = resolve_secret_refs(entry.get("config", {}) or {})
                
                if tool_name in self._available_tools_map:
                    try:
                        ToolClass = self._available_tools_map[tool_name]
                        tools.append(ToolClass(**tool_config))
                        loaded_names.add(tool_name)
                        logger.info(f"Loaded tool: {tool_name}")
                    except Exception as e:
                        logger.error(f"Failed to load tool {tool_name}: {e}")

        if OpenClawTools:
            # 延迟导入以防止模块初始化时发生循环依赖
            from app.core.config import settings
            if settings.OPENCLAW_BASE_URL:
                try:
                    tools.append(OpenClawTools())
                    logger.info("Loaded OpenClawTools")
                except Exception as e:
                    logger.error(f"Failed to load OpenClawTools: {e}")

        should_enable_search = enable_search or ("duckduckgo" in tools_config and "duckduckgo" not in loaded_names)
        
        if should_enable_search:
            from app.core.config import settings
            
            tavily_loaded = False
            if settings.TAVILY_API_KEY:
                try:
                    from app.services.eah_agent.tools.libs.search_tools import TavilyTools
                    tools.append(TavilyTools(api_key=settings.TAVILY_API_KEY))
                    tavily_loaded = True
                    logger.info("Loaded TavilyTools (Auto-replacement for DuckDuckGo)")
                except ImportError:
                    logger.warning("Tavily configured but import failed.")
            
            if not tavily_loaded:
                import os
                ddg_kwargs = {}
                proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
                if proxy:
                    ddg_kwargs["proxy"] = proxy
                tools.append(DuckDuckGoTools(**ddg_kwargs))

        is_sandbox_enabled = skills_config.get("sandbox", {}).get("enabled")
        if not is_sandbox_enabled and isinstance(tools_config, list):
            for t in tools_config:
                if isinstance(t, str) and t.startswith("sb_"):
                    is_sandbox_enabled = True
                    break
        
        if is_sandbox_enabled:
            try:
                tools.append(SandboxTools(session_id=session_id))
                logger.info("Loaded SandboxTools")
            except Exception as e:
                logger.error(f"Failed to load SandboxTools: {e}")

        knowledge_config = getattr(agent_model, "knowledge_config", None)
        has_documents = False
        if knowledge_config and isinstance(knowledge_config, dict):
            has_documents = bool(knowledge_config.get("document_ids"))
            
        if (knowledge_config or has_documents) and HAS_KNOWLEDGE_TOOLS:
            tools.extend([search_knowledge_base, query_knowledge_graph])
            logger.info("Loaded Knowledge Base Tools")
            
        file_skills_config = skills_config.get("file_skills", {})
        if file_skills_config.get("enabled", False):
            try:
                from app.services.eah_agent.skills.toolkit import SkillToolkit
                skills_path_str = file_skills_config.get("path", "app/data/skills")
                
                skill_toolkit = SkillToolkit(skills_path=skills_path_str)
                tools.append(skill_toolkit)
                logger.info(f"Injected SkillToolkit for path: {skills_path_str}")
                
            except Exception as e:
                logger.error(f"Failed to load file skills: {e}")

        for custom_tool in self._custom_tools:
            try:
                if isinstance(custom_tool, type):
                    tools.append(custom_tool())
                else:
                    tools.append(custom_tool)
            except Exception as e:
                logger.error(f"Failed to load custom tool {custom_tool}: {e}")

        if mcp_config:
            from .factory import get_mcp_toolkit
            for mcp_server in mcp_config:
                try:
                    toolkit = await get_mcp_toolkit(mcp_server, agent_id=agent_model.id)
                    tools.append(toolkit)
                except Exception as e:
                    logger.error(f"Failed to load MCP tool {mcp_server}: {e}")

        return tools

default_tools = ToolsManager()
