import logging
import asyncio
from typing import Dict, Any, Union

from agno.tools import Toolkit
from app.services.mcp_client import mcp_pool
from app.services.agent.tools.mcp_tool import MCPToolkit as LegacyWSToolkit
# Import the Agno implementation from local path
from app.services.tools.mcp.mcp import MCPTools as AgnoMCPTools

logger = logging.getLogger(__name__)

async def get_mcp_toolkit(config: Dict[str, Any], agent_id: str = None) -> Toolkit:
    """
    Factory to return the appropriate MCP Toolkit based on protocol.
    
    Args:
        config: MCP server configuration dictionary.
                Supported keys:
                - url: WebSocket (ws://) or HTTP (http://) URL
                - command: Command to run for stdio transport
                - type: Optional type hint (e.g., "sse")
        agent_id: Optional agent ID for context injection
        
    Returns:
        A Toolkit instance (either LegacyWSToolkit or AgnoMCPTools)
    """
    url = config.get("url")
    command = config.get("command")
    
    # Case 1: WebSocket (Legacy/Existing Path)
    # This handles the existing WebSocket implementation which is proven for RAG
    if url and (url.startswith("ws://") or url.startswith("wss://")):
        logger.info(f"Using Legacy WebSocket MCP Client for {url}")
        client = await mcp_pool.get_client(url)
        # Ensure connected
        await client.connect()
        # Fetch tools immediately to register them
        tools_list = await client.list_tools()
        return LegacyWSToolkit(client, tools_list)
        
    # Case 2: Stdio / HTTP / SSE (New Agno Path)
    # This enables local execution and standard HTTP/SSE servers
    elif command or (url and url.startswith("http")):
        logger.info(f"Using Agno MCP Tools for {'stdio' if command else url}")
        
        # Determine transport
        transport = "stdio"
        if url:
            transport = "streamable-http"
            if config.get("type") == "sse" or "sse" in str(config.get("transport", "")).lower():
                transport = "sse"
        
        # Define header provider for dynamic context injection
        def _header_provider(run_context=None, agent=None, **kwargs):
            headers = {}
            if agent_id:
                headers["X-Agent-ID"] = agent_id
            if run_context and hasattr(run_context, "run_id"):
                headers["X-Run-ID"] = run_context.run_id
            return headers

        # Create Agno toolkit instance
        toolkit = AgnoMCPTools(
            command=command,
            url=url,
            transport=transport,
            header_provider=_header_provider,
            # Pass environment variables if needed
            env=config.get("env"),
            # Include/exclude tools if configured
            include_tools=config.get("include_tools"),
            exclude_tools=config.get("exclude_tools")
        )
        
        # Initialize connection
        # Note: Agno tools are lazy-loaded, but we connect here to fail fast if config is bad
        await toolkit.initialize()
        
        return toolkit
    
    raise ValueError(f"Invalid MCP configuration: must provide 'url' (ws/http) or 'command'. Config: {config}")
