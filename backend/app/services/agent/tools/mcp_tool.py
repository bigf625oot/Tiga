import json
import logging
from typing import List, Dict, Any, Callable, Optional
from agno.tools import Toolkit
from app.services.mcp_client import MCPClient

logger = logging.getLogger(__name__)

class MCPToolkit(Toolkit):
    """
    Agno Toolkit adapter for MCP (Model Context Protocol).
    """
    def __init__(self, client: MCPClient, tools_list: List[Dict], **kwargs):
        name = f"mcp_{client.client_id}" if client.client_id else "mcp_tools"
        super().__init__(name=name, **kwargs)
        self.client = client
        self.tools_metadata = tools_list
        self.tool_map = {}
        self._register_tools()

    def _register_tools(self):
        """
        Register MCP tools as callables in the Toolkit.
        """
        for tool_def in self.tools_metadata:
            name = tool_def["name"]
            description = tool_def.get("description", "")
            # We don't have the schema validation here yet, as Agno usually inspects function signatures.
            # However, for the purpose of 'agent_execute_step.py' which might extract tools manually,
            # we mainly need the callable to exist.
            
            # We create a wrapper that delegates to the MCP client
            # We use a closure to capture 'name'
            async def tool_wrapper(**kwargs):
                """
                Dynamic MCP Tool Wrapper
                """
                logger.info(f"Calling MCP tool {name} with args: {kwargs}")
                try:
                    result = await self.client.call_tool(name, kwargs)
                    return json.dumps(result, ensure_ascii=False)
                except Exception as e:
                    logger.error(f"MCP Tool {name} failed: {e}")
                    return f"Error: {str(e)}"

            # Set metadata
            tool_wrapper.__name__ = name
            tool_wrapper.__doc__ = description
            
            # Register with the Toolkit
            self.register(tool_wrapper)
            self.tool_map[name] = tool_wrapper

    def get_openai_tools(self) -> List[Dict]:
        """
        Convert MCP tool definitions to OpenAI function schemas.
        Used by DeepSeek path in agent_execute_step.py.
        """
        openai_tools = []
        for tool in self.tools_metadata:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("inputSchema", {})
                }
            })
        return openai_tools
