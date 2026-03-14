"""
Tool Factory:
Factory to create and configure tool instances.
核心功能：
1. 发现并注册所有可用的工具类。
2. 根据工具名称创建工具实例。
3. 检查工具是否可用（依赖是否安装，API密钥是否配置等）。
"""
import logging
from typing import Dict, Type, Any, Optional
from agno.tools import Toolkit

from app.services.eah_agent.tools.registry import discover_tools, check_tool_availability

logger = logging.getLogger(__name__)

class ToolFactory:
    """
    Factory to create and configure tool instances.
    """
    _tool_classes: Dict[str, Type[Toolkit]] = {}
    _initialized = False

    @classmethod
    def initialize(cls):
        """
        Discovers and registers all available tools.
        """
        if cls._initialized:
            return
            
        try:
            cls._tool_classes = discover_tools(include_metadata=False)
            logger.info(f"Discovered {len(cls._tool_classes)} tools.")
            cls._initialized = True
        except Exception as e:
            logger.error(f"Failed to discover tools: {e}")

    @classmethod
    def get_tool_class(cls, name: str) -> Optional[Type[Toolkit]]:
        """
        Get the tool class by name.
        """
        if not cls._initialized:
            cls.initialize()
        return cls._tool_classes.get(name)

    @classmethod
    def create_tool(cls, name: str, config: Dict[str, Any] = None) -> Optional[Toolkit]:
        """
        Create a tool instance by name with optional configuration.
        """
        if not cls._initialized:
            cls.initialize()
            
        tool_cls = cls._tool_classes.get(name)
        if not tool_cls:
            logger.warning(f"Tool '{name}' not found.")
            return None
            
        if not check_tool_availability(tool_cls):
            logger.warning(f"Tool '{name}' is not available (missing dependencies or keys).")
            return None
            
        config = config or {}
        try:
            # Check if config matches what the tool expects
            # For simplicity, we pass config as kwargs, assuming the tool constructor handles it
            # or the config keys match __init__ args.
            return tool_cls(**config)
        except Exception as e:
            logger.error(f"Failed to instantiate tool '{name}': {e}")
            return None
