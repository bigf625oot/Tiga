import logging
from typing import List, Dict, Any, Callable, Optional


logger = logging.getLogger("eah.components.tools")

class DefaultToolRegistry:
    """
    默认的 ToolRegistry 实现。
    目前包装内存字典，未来可整合 `tools/registry.py` 的现有逻辑。
    """
    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}

    def register_tool(self, name: str, func: Callable, description: str) -> None:
        self._tools[name] = {
            "func": func,
            "description": description
        }
        logger.debug(f"Tool registered: {name}")

    def get_tool(self, name: str) -> Optional[Callable]:
        tool_data = self._tools.get(name)
        return tool_data["func"] if tool_data else None

    def get_all_tool_schemas(self) -> List[Dict[str, Any]]:
        # 实际实现中需要反射 func 提取参数 schema，这里简化
        schemas = []
        for name, data in self._tools.items():
            schemas.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": data["description"]
                }
            })
        return schemas
