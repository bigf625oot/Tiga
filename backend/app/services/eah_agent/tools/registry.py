import importlib
import inspect
import pkgutil
from pathlib import Path
from typing import Dict, Type, Any, List, Union
from pydantic import BaseModel

from agno.tools import Toolkit

# Define directories to search for tools
# Trigger reload for new tools
TOOL_DIRECTORIES = [
    Path(__file__).parent / "libs",  # app/services/eah_agent/tools/libs/
    Path(__file__).parent.parent / "skills", # app/services/eah_agent/skills/
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
    # 统一使用 _description 或 description 属性，回退至 docstring，以保证元数据的一致性
    description = "暂无描述"
    if hasattr(tool_class, "_description"):
        description = tool_class._description
    elif hasattr(tool_class, "description") and isinstance(tool_class.description, str):
        description = tool_class.description
    elif tool_class.__doc__:
        description = tool_class.__doc__.strip().split("\n")[0]
    
    category = "integration"
    if hasattr(tool_class, "_category"):
        category = tool_class._category
    elif hasattr(tool_class, "category"):
        category = tool_class.category
    
    label = tool_name
    if hasattr(tool_class, "_label"):
        label = tool_class._label
    elif hasattr(tool_class, "label"):
        label = tool_class.label

    # 利用 Pydantic 的内部方法导出 schema，或者使用自定义的 config_schema
    config_schema = {}
    if hasattr(tool_class, "Config") and inspect.isclass(tool_class.Config):
        try:
            config_schema = tool_class.Config.model_json_schema()
        except Exception:
            pass
    elif hasattr(tool_class, "config_schema"):
         config_schema = tool_class.config_schema

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
        elif tools_dir.name == "skills" and tools_dir.parent.name == "eah_agent":
            base_package = "app.services.eah_agent.skills"
        else:
            continue

        for module_info in pkgutil.iter_modules([str(tools_dir)]):
            module_name = module_info.name
            
            if module_name in ["discovery", "mcp_toolbox", "__init__", "factory", "runner", "mcp_tool", "manager", "loaders", "utils", "errors", "validator", "skill"]:
                continue
                
            try:
                module = importlib.import_module(f"{base_package}.{module_name}")
                
                found_tools = []
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, Toolkit) and obj is not Toolkit:
                        if obj.__module__ == module.__name__:
                            found_tools.append(obj)
                
                for obj in found_tools:
                    tool_key = None
                    
                    # 优先使用显式的 _name 属性来防止重命名引发的键值冲突
                    if hasattr(obj, "_name"):
                        tool_key = obj._name
                    
                    if not tool_key:
                        import re
                        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', obj.__name__)
                        tool_key = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
                    
                    tools[tool_key] = obj
                    
                    if include_metadata:
                         metadata_list.append(get_tool_metadata(obj, tool_key))

            except ImportError as e:
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
