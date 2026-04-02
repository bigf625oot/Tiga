import logging
from typing import List, Dict, Any, Optional
from agno.tools import Toolkit
from .provider import CapabilityProvider
from app.services.platform.mcp.ws_client import mcp_pool
from app.services.agent.tools.libs.mcp_tool import MCPToolkit as LegacyWSToolkit
from app.services.agent.tools.mcp.mcp import MCPTools as AgnoMCPTools

logger = logging.getLogger(__name__)

class MCPCapabilityProvider(CapabilityProvider):
    """
    统一的 MCP 能力提供者
    消除了原来零散的 LegacyWSToolkit, AgnoMCPTools, MCPToolbox 等实现，
    由这里统一根据协议（ws/http/stdio）委托给对应的实现。
    """
    
    def __init__(self, mcp_configs: List[Dict[str, Any]], agent_id: Optional[str] = None):
        self.mcp_configs = mcp_configs or []
        self.agent_id = agent_id
        
    @property
    def provider_type(self) -> str:
        return "mcp"
        
    async def get_tools(self) -> List[Toolkit]:
        import asyncio
        
        toolkits = []
        tasks = []
        
        for config in self.mcp_configs:
            tasks.append(self._create_toolkit(config))
            
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for config, result in zip(self.mcp_configs, results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to load MCP tool config {config}: {result}")
                else:
                    toolkits.append(result)
                    
        return toolkits

    async def _create_toolkit(self, config: Dict[str, Any]) -> Toolkit:
        """根据协议类型创建对应的 MCP Toolkit 实例"""
        url = config.get("url")
        command = config.get("command")
        
        if url and (url.startswith("ws://") or url.startswith("wss://")):
            logger.info(f"Using Legacy WebSocket MCP Client for {url}")
            client = await mcp_pool.get_client(url)
            await client.connect()
            tools_list = await client.list_tools()
            return LegacyWSToolkit(client, tools_list)
            
        elif command or (url and url.startswith("http")):
            logger.info(f"Using Agno MCP Tools for {'stdio' if command else url}")
            transport = "stdio"
            if url:
                transport = "streamable-http"
                if config.get("type") == "sse" or "sse" in str(config.get("transport", "")).lower():
                    transport = "sse"
            
            def _header_provider(run_context=None, agent=None, **kwargs):
                headers = {}
                if self.agent_id:
                    headers["X-Agent-ID"] = self.agent_id
                if run_context and hasattr(run_context, "run_id"):
                    headers["X-Run-ID"] = run_context.run_id
                return headers

            toolkit = AgnoMCPTools(
                command=command,
                url=url,
                transport=transport,
                header_provider=_header_provider,
                env=config.get("env"),
                include_tools=config.get("include_tools"),
                exclude_tools=config.get("exclude_tools")
            )
            
            await toolkit.initialize()
            return toolkit
            
        raise ValueError(f"Invalid MCP configuration: must provide 'url' (ws/http) or 'command'. Config: {config}")

    def get_system_prompt_snippet(self) -> Optional[str]:
        return None
