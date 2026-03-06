import importlib
import inspect
import pkgutil
import sys
from pathlib import Path
from typing import Dict, Type, Any

from agno.tools import Toolkit

TOOLS_DIR = Path(__file__).parent

def discover_tools() -> Dict[str, Type[Toolkit]]:
    """
    Discover all available tool classes in the tools directory.
    Returns a dictionary mapping tool names (module names) to tool classes.
    """
    tools = {}
    
    # Iterate over all modules in the current directory
    for module_info in pkgutil.iter_modules([str(TOOLS_DIR)]):
        module_name = module_info.name
        
        # Skip internal modules
        if module_name in ["discovery", "mcp_toolbox", "__init__"]:
            continue
            
        try:
            # Import the module
            module = importlib.import_module(f"app.services.tools.{module_name}")
            
            # Find the tool class in the module
            # We look for a class that inherits from Toolkit and is defined in this module
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, Toolkit) and obj is not Toolkit:
                    # Check if the class is actually defined in this module
                    # (to avoid picking up imported Toolkits)
                    if obj.__module__ == module.__name__:
                        tools[module_name] = obj
                        break
        except ImportError as e:
            # Log error but continue discovery
            print(f"Error importing tool module {module_name}: {e}")
            continue
            
    return tools

def check_tool_availability(tool_class: Type[Toolkit]) -> bool:
    """
    Check if a tool is available for use (e.g. has required API keys).
    """
    if hasattr(tool_class, "is_available"):
        if callable(tool_class.is_available):
            return tool_class.is_available()
        return bool(tool_class.is_available)
    return True

def get_tool_category(tool_class: Type[Toolkit]) -> str:
    """
    Get the category of a tool.
    """
    if hasattr(tool_class, "_category"):
        return tool_class._category
    if hasattr(tool_class, "category"):
        return tool_class.category
    return "integration"
