from .registry import discover_tools as discover_tools, ToolMetadata as ToolMetadata
from .tool_factory import ToolFactory as ToolFactory
from .loader import default_tools, ToolsManager as ToolsManager

# Convenient function for adding custom tools
add_tool = default_tools.add_tool
