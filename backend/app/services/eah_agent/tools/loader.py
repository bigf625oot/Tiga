from typing import List, Dict, Any, Optional, Type, Union
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from agno.tools import Toolkit

# Import standard tools
from .libs.duckduckgo import DuckDuckGoTools
from .libs.sandbox_tools import SandboxTools
from .registry import discover_tools

# Import special tools (wrapped to avoid import errors if dependencies missing)
try:
    from app.services.openclaw import OpenClawTools
except ImportError:
    OpenClawTools = None

try:
    from app.tools.n8n import N8NTools
except ImportError:
    N8NTools = None

try:
    from app.services.rag.mcp_server import search_knowledge_base, query_knowledge_graph
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
        
    async def load_tools(self, agent_model: Any, db: AsyncSession = None, session_id: str = None) -> List[Any]:
        """
        Load all tools based on agent configuration and defaults.
        This replaces the hardcoded logic in AgentManager.
        """
        tools = []
        
        # 1. Configured Tools from DB (agent_model.tools_config)
        tools_config = getattr(agent_model, "tools_config", []) or []
        skills_config = getattr(agent_model, "skills_config", {}) or {}
        mcp_config = getattr(agent_model, "mcp_config", []) or []
        
        # 2. Load Dynamic Tools (from libs/)
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
                    tool_config = entry.get("config", {})
                
                if tool_name in self._available_tools_map:
                    try:
                        ToolClass = self._available_tools_map[tool_name]
                        tools.append(ToolClass(**tool_config))
                        loaded_names.add(tool_name)
                        logger.info(f"Loaded tool: {tool_name}")
                    except Exception as e:
                        logger.error(f"Failed to load tool {tool_name}: {e}")

        # 3. Load Special/Hardcoded Tools (Refactored)
        
        # OpenClaw
        if OpenClawTools:
            # Check settings via imports inside method to avoid circular deps if any
            from app.core.config import settings
            if settings.OPENCLAW_BASE_URL:
                try:
                    tools.append(OpenClawTools())
                    logger.info("Loaded OpenClawTools")
                except Exception as e:
                    logger.error(f"Failed to load OpenClawTools: {e}")

        # DuckDuckGo (Fallback if not explicitly configured but search enabled)
        if "duckduckgo" in tools_config and "duckduckgo" not in loaded_names:
            tools.append(DuckDuckGoTools())

        # Sandbox
        is_sandbox_enabled = skills_config.get("sandbox", {}).get("enabled")
        if not is_sandbox_enabled and isinstance(tools_config, list):
            for t in tools_config:
                if isinstance(t, str) and t.startswith("sb_"):
                    is_sandbox_enabled = True
                    break
        
        if is_sandbox_enabled:
            try:
                # SandboxTools needs session_id
                tools.append(SandboxTools(session_id=session_id))
                logger.info("Loaded SandboxTools")
            except Exception as e:
                logger.error(f"Failed to load SandboxTools: {e}")

        # N8N
        if N8NTools and "n8n" in tools_config and db:
            try:
                from app.models.workflow import Workflow
                from sqlalchemy import select
                wf_res = await db.execute(select(Workflow).filter(Workflow.is_active == True))
                workflows = wf_res.scalars().all()
                if workflows:
                    wf_dicts = [{"name": w.name, "webhook_url": w.webhook_url} for w in workflows]
                    tools.append(N8NTools(workflows=wf_dicts))
            except Exception as e:
                logger.error(f"Failed to load N8NTools: {e}")

        # Knowledge Base
        knowledge_config = getattr(agent_model, "knowledge_config", None)
        has_documents = False
        if knowledge_config and isinstance(knowledge_config, dict):
            has_documents = bool(knowledge_config.get("document_ids"))
            
        if (knowledge_config or has_documents) and HAS_KNOWLEDGE_TOOLS:
            tools.extend([search_knowledge_base, query_knowledge_graph])
            logger.info("Loaded Knowledge Base Tools")
            
        # File Skills (Unified Handling)
        file_skills_config = skills_config.get("file_skills", {})
        if file_skills_config.get("enabled", False):
            try:
                from app.services.eah_agent.skills.toolkit import SkillToolkit
                skills_path_str = file_skills_config.get("path", "app/data/skills")
                
                # Use the unified SkillToolkit
                skill_toolkit = SkillToolkit(skills_path=skills_path_str)
                tools.append(skill_toolkit)
                logger.info(f"Injected SkillToolkit for path: {skills_path_str}")
                
            except Exception as e:
                logger.error(f"Failed to load file skills: {e}")

        # 4. Load Custom Added Tools
        for custom_tool in self._custom_tools:
            try:
                if isinstance(custom_tool, type):
                    tools.append(custom_tool())
                else:
                    tools.append(custom_tool)
            except Exception as e:
                logger.error(f"Failed to load custom tool {custom_tool}: {e}")

        # 5. MCP Tools (Delegated to factory)
        if mcp_config:
            from .factory import get_mcp_toolkit
            for mcp_server in mcp_config:
                try:
                    toolkit = await get_mcp_toolkit(mcp_server, agent_id=agent_model.id)
                    tools.append(toolkit)
                except Exception as e:
                    logger.error(f"Failed to load MCP tool {mcp_server}: {e}")

        return tools

# Singleton instance
default_tools = ToolsManager()
