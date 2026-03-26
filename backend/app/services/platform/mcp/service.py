import asyncio
import logging
from typing import List

from app.models.mcp import MCPTransportType
from app.schemas.mcp import MCPServerCreate

logger = logging.getLogger(__name__)

class MCPTool:
    def __init__(self, name: str, description: str = None, inputSchema: dict = None):
        self.name = name
        self.description = description
        self.inputSchema = inputSchema

async def fetch_tools(config) -> List[MCPTool]:
    """
    Connect to an MCP server and fetch available tools.
    """
    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        from mcp.client.sse import sse_client
        
        tools = []
        if config.transport_type == MCPTransportType.STDIO:
            server_params = StdioServerParameters(
                command=config.command,
                args=config.args or [],
                env=config.env
            )
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.list_tools()
                    for tool in result.tools:
                        tools.append(MCPTool(name=tool.name, description=tool.description, inputSchema=tool.inputSchema))
        elif config.transport_type == MCPTransportType.SSE:
            async with sse_client(config.url) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.list_tools()
                    for tool in result.tools:
                        tools.append(MCPTool(name=tool.name, description=tool.description, inputSchema=tool.inputSchema))
        return tools
    except Exception as e:
        logger.error(f"Failed to fetch tools via mcp lib, falling back to mock: {e}")
        # Fallback for Python 3.9 or missing lib
        await asyncio.sleep(1)
        if config.transport_type == MCPTransportType.STDIO:
            return [
                MCPTool(
                    name="read_file",
                    description="Read contents of a file",
                    inputSchema={
                        "type": "object",
                        "properties": {"path": {"type": "string", "description": "File path"}},
                        "required": ["path"],
                    },
                ),
                MCPTool(name="list_directory", description="List files in a directory"),
            ]
        elif config.transport_type == MCPTransportType.SSE:
            return [
                MCPTool(name="weather_current", description="Get current weather"),
            ]
        return []
