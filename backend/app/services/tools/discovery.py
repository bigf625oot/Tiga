import importlib
import inspect
import pkgutil
import logging
from pathlib import Path
from typing import Dict, Type, List, Any
from agno.tools import Toolkit

logger = logging.getLogger(__name__)

TOOLS_PACKAGE = "app.services.tools"
TOOLS_DIR = Path(__file__).parent

from functools import lru_cache

@lru_cache(maxsize=1)
def discover_tools() -> Dict[str, Type[Toolkit]]:
    """
    Scans the tools directory and returns a map of tool_name -> ToolkitClass.
    It relies on the convention that the module name corresponds to the tool name.
    Cached to avoid re-scanning on every call.
    """
    found_tools = {}
    
    # Iterate over all modules in the package
    for module_info in pkgutil.iter_modules([str(TOOLS_DIR)]):
        if module_info.name.startswith('_') or module_info.name in ['mcp', 'models', 'streamlit']:
            continue
            
        try:
            module_path = f"{TOOLS_PACKAGE}.{module_info.name}"
            module = importlib.import_module(module_path)
            
            # Find classes inheriting from Toolkit
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, Toolkit) and obj is not Toolkit:
                    # We found a Toolkit class.
                    # Use the module name as the unique key (e.g., 'calculator')
                    # This maps 'calculator' -> CalculatorTools
                    found_tools[module_info.name] = obj
                    break # Assuming one main Toolkit per file
        except Exception as e:
            logger.error(f"Failed to load tool module {module_info.name}: {e}")
            
    return found_tools

def check_tool_availability(tool_class: Type[Toolkit]) -> bool:
    """
    Checks if a tool is available for use (e.g., has required env vars).
    Looks for an 'is_available' class method on the tool.
    Defaults to True if no check is defined.
    """
    if hasattr(tool_class, "is_available") and callable(getattr(tool_class, "is_available")):
        try:
            return tool_class.is_available()
        except Exception as e:
            logger.warning(f"Error checking availability for {tool_class.__name__}: {e}")
            return False
    return True

def get_tool_category(tool_class: Type[Toolkit]) -> str:
    """
    Determines the category of a tool.
    Looks for a '_category' or 'category' attribute on the tool class.
    Defaults to 'integration'.
    """
    if hasattr(tool_class, "_category"):
        return getattr(tool_class, "_category")
    if hasattr(tool_class, "category"):
        return getattr(tool_class, "category")
    return "integration"

def get_tool_metadata(tool_name: str, tool_class: Type[Toolkit]) -> Dict[str, Any]:
    """
    Extracts metadata from a Toolkit class for registration.
    """
    doc = tool_class.__doc__ or ""
    # Clean up docstring
    description = doc.strip().split('\n')[0] if doc else f"{tool_name.capitalize()} tool"
    
    return {
        "name": tool_name.capitalize(), # Display name
        "description": description,
        "category": get_tool_category(tool_class), 
        "author": "Tiga",
        "version": "1.0.0",
        "is_official": True,
        # We can store the module path in meta_data if needed
        "meta_data": {
            "module": f"{TOOLS_PACKAGE}.{tool_name}",
            "class": tool_class.__name__
        }
    }
