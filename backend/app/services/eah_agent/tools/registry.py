import importlib
import inspect
import pkgutil
import re
from pathlib import Path
from typing import Dict, Type, Any, List, Optional, Union
from pydantic import BaseModel

from agno.tools import Toolkit

# Define directories to search for tools
# Trigger reload for new tools
TOOL_DIRECTORIES = [
    Path(__file__).parent / "libs",  # app/services/eah_agent/tools/libs/
]

class ToolMetadata(BaseModel):
    name: str
    label: str
    description: str
    category: str = "integration"
    config_schema: Dict[str, Any] = {}
    is_available: bool = True

def get_tool_metadata(tool_class: Type[Toolkit], tool_name: str) -> ToolMetadata:
    """
    Extract metadata from a tool class.
    """
    # 1. Description
    # Prefer _description or description attribute if available
    description = "暂无描述"
    if hasattr(tool_class, "_description"):
        description = tool_class._description
    elif hasattr(tool_class, "description") and isinstance(tool_class.description, str):
        description = tool_class.description
    elif tool_class.__doc__:
        description = tool_class.__doc__.strip().split("\n")[0]
    
    # 2. Category
    category = "integration"
    if hasattr(tool_class, "_category"):
        category = tool_class._category
    elif hasattr(tool_class, "category"):
        category = tool_class.category
    
    # 3. Label (Display Name)
    label = tool_name
    if hasattr(tool_class, "_label"):
        label = tool_class._label
    elif hasattr(tool_class, "label"):
        label = tool_class.label
    # 4. Config Schema (JSON Schema)
    # We look for a 'Config' inner class or 'config_schema' attribute
    config_schema = {}
    if hasattr(tool_class, "Config") and inspect.isclass(tool_class.Config):
         # If using Pydantic model for config
         try:
             config_schema = tool_class.Config.model_json_schema()
         except:
             pass
    elif hasattr(tool_class, "config_schema"):
         config_schema = tool_class.config_schema

    # 5. Availability
    is_available = True
    if hasattr(tool_class, "is_available"):
        if callable(tool_class.is_available):
            is_available = tool_class.is_available()
        else:
            is_available = bool(tool_class.is_available)

    return ToolMetadata(
        name=tool_name,
        label=label,
        description=description,
        category=category,
        config_schema=config_schema,
        is_available=is_available
    )

def discover_tools(include_metadata: bool = False) -> Union[Dict[str, Type[Toolkit]], List[ToolMetadata]]:
    """
    Discover all available tool classes in the tools directories.
    
    Args:
        include_metadata: If True, returns a list of ToolMetadata objects.
                          If False, returns a dict mapping names to classes.
    """
    tools = {}
    metadata_list = []
    
    for tools_dir in TOOL_DIRECTORIES:
        if not tools_dir.exists():
            continue

        # Determine base package based on directory
        if tools_dir.name == "libs" and tools_dir.parent.name == "tools":
            base_package = "app.services.eah_agent.tools.libs"
        else:
            continue

        for module_info in pkgutil.iter_modules([str(tools_dir)]):
            module_name = module_info.name
            
            # Skip internal modules
            if module_name in ["discovery", "mcp_toolbox", "__init__", "factory", "runner", "mcp_tool"]:
                continue
                
            try:
                # Import the module
                module = importlib.import_module(f"{base_package}.{module_name}")
                
                # Find all tool classes in the module
                found_tools = []
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, Toolkit) and obj is not Toolkit:
                        # Check if the class is actually defined in this module
                        if obj.__module__ == module.__name__:
                            found_tools.append(obj)
                
                for obj in found_tools:
                    # Determine unique key for the tool
                    tool_key = None
                    
                    # 1. Prefer explicit _name class attribute
                    if hasattr(obj, "_name"):
                        tool_key = obj._name
                    
                    # 2. Fallback to class name converted to snake_case
                    if not tool_key:
                        import re
                        # Convert CamelCase to snake_case
                        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', obj.__name__)
                        tool_key = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
                        
                        # Remove '_tools' suffix for cleaner names if present, 
                        # unless it results in empty or too short? 
                        # Actually, keeping _tools is safer to avoid conflict with module names sometimes.
                        # But users prefer 'website' over 'website_tools'.
                        # Let's keep it simple: use snake_case class name.
                    
                    # 3. Compatibility: If module has only one tool, also register it under module name?
                    # This helps with 'duckduckgo' -> 'duckduckgo.py'
                    # But if 'duckduckgo.py' has 'DuckDuckGoTools', snake_case is 'duck_duck_go_tools'.
                    # User expects 'duckduckgo'.
                    # So if I don't change existing code, I should manually map or ensure `_name` is set.
                    
                    # Let's rely on _name if I add it.
                    
                    tools[tool_key] = obj
                    
                    if include_metadata:
                         # Use tool_key as name in metadata
                         metadata_list.append(get_tool_metadata(obj, tool_key))

            except ImportError as e:
                # Log error but continue discovery
                print(f"Error importing tool module {module_name}: {e}")
                with open("discovery_errors.log", "a") as f:
                    f.write(f"Error importing {module_name}: {e}\n")
                continue
            except Exception as e:
                print(f"Error loading tool {module_name}: {e}")
                with open("discovery_errors.log", "a") as f:
                    f.write(f"Error loading {module_name}: {e}\n")
                continue
            
    if include_metadata:
        return metadata_list
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
    elif hasattr(tool_class, "category"):
        return tool_class.category
    return "integration"
