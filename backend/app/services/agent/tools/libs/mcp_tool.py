import json
import logging
import inspect
from typing import List, Dict, Any
from agno.tools import Toolkit
from app.services.platform.mcp.ws_client import MCPClient

logger = logging.getLogger(__name__)

def _mcp_schema_to_python_type(schema_type: str) -> Any:
    """Map JSON Schema types to Python types for inspect.Parameter annotation."""
    mapping = {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "array": list,
        "object": dict,
    }
    return mapping.get(schema_type, Any)

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
            input_schema = tool_def.get("inputSchema", {})
            
            # We create a wrapper that delegates to the MCP client
            # We use a closure to capture 'name' - Use default argument to break closure binding issue
            async def tool_wrapper(name=name, **kwargs):
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
            
            # Rewrite signature so Agno can infer parameters correctly
            sig = inspect.signature(tool_wrapper)
            params = []
            
            properties = input_schema.get("properties", {})
            required_fields = input_schema.get("required", [])
            
            for param_name, param_info in properties.items():
                param_type_str = param_info.get("type", "string")
                python_type = _mcp_schema_to_python_type(param_type_str)
                
                is_required = param_name in required_fields
                default_value = inspect.Parameter.empty if is_required else None
                
                # Create the parameter
                param = inspect.Parameter(
                    name=param_name,
                    kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    default=default_value,
                    annotation=python_type
                )
                params.append(param)
                
            tool_wrapper.__signature__ = sig.replace(parameters=params)
            
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
