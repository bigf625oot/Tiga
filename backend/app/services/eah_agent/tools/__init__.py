from .registry import discover_tools, ToolMetadata
from .factory import get_mcp_toolkit
from .loader import default_tools, ToolsManager

# Convenient function for adding custom tools
add_tool = default_tools.add_tool
