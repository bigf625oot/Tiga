import logging
from typing import List, Dict, Any, Optional
from agno.tools import Toolkit
from .provider import CapabilityProvider
from app.services.agent.tools.registry import discover_tools
from app.services.agent.utils.secret_refs import resolve_secret_refs

logger = logging.getLogger(__name__)

class LocalCapabilityProvider(CapabilityProvider):
    """
    本地工具能力提供者：负责加载内置的 DuckDuckGo, Sandbox, OpenClaw 等工具
    """
    
    def __init__(self, tools_config: List[Any], enable_search: bool = False, session_id: Optional[str] = None):
        self.tools_config = tools_config or []
        self.enable_search = enable_search
        self.session_id = session_id
        self._available_tools_map = discover_tools()
        
    @property
    def provider_type(self) -> str:
        return "local"
        
    async def get_tools(self) -> List[Toolkit]:
        tools = []
        loaded_names = set()
        
        # 1. 动态加载按名配置的工具
        for entry in self.tools_config:
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
                    
                    # 架构防线：在实例化前进行确定性可用性检查
                    # 避免引发隐式或延迟的 ImportError
                    is_available = True
                    if hasattr(ToolClass, "is_available"):
                        is_available = ToolClass.is_available() if callable(ToolClass.is_available) else bool(ToolClass.is_available)
                        
                    if not is_available:
                        logger.warning(f"Tool {tool_name} is in tools_config but marked as unavailable (possibly missing dependencies).")
                        continue

                    tools.append(ToolClass(**tool_config))
                    loaded_names.add(tool_name)
                    logger.info(f"Loaded local tool: {tool_name}")
                except Exception as e:
                    logger.error(f"Failed to load tool {tool_name}: {e}")

        # 2. 搜索工具 (DuckDuckGo / Tavily)
        should_enable_search = self.enable_search or ("duckduckgo" in self.tools_config and "duckduckgo" not in loaded_names)
        if should_enable_search:
            from app.core.config import settings
            tavily_loaded = False
            
            if settings.TAVILY_API_KEY:
                try:
                    from app.services.agent.tools.libs.search_tools import TavilyTools
                    tools.append(TavilyTools(api_key=settings.TAVILY_API_KEY))
                    tavily_loaded = True
                    logger.info("Loaded TavilyTools (Auto-replacement for DuckDuckGo)")
                except ImportError:
                    logger.warning("Tavily configured but import failed.")
                    
            if not tavily_loaded:
                from app.services.agent.tools.libs.duckduckgo import DuckDuckGoTools
                import os
                ddg_kwargs = {}
                proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
                if proxy:
                    ddg_kwargs["proxy"] = proxy
                tools.append(DuckDuckGoTools(**ddg_kwargs))
                
        # 3. 沙箱工具
        is_sandbox_enabled = False
        for t in self.tools_config:
            if isinstance(t, str) and t.startswith("sb_"):
                is_sandbox_enabled = True
                break
            if isinstance(t, dict) and t.get("name", "").startswith("sb_"):
                is_sandbox_enabled = True
                break
                
        if is_sandbox_enabled:
            from app.services.agent.tools.libs.sandbox_tools import SandboxTools
            try:
                tools.append(SandboxTools(session_id=self.session_id))
                logger.info("Loaded SandboxTools")
            except Exception as e:
                logger.error(f"Failed to load SandboxTools: {e}")

        return tools
        
    def get_system_prompt_snippet(self) -> Optional[str]:
        return None
