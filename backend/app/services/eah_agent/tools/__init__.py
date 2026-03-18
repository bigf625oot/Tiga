from .registry import discover_tools as discover_tools, ToolMetadata as ToolMetadata
from .factory import get_mcp_toolkit as get_mcp_toolkit
from .loader import default_tools, ToolsManager as ToolsManager

# Convenient function for adding custom tools
add_tool = default_tools.add_tool
