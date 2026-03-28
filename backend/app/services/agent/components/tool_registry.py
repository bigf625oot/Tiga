import inspect
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger("eah.components.tools")


@dataclass(slots=True)
class ToolDefinition:
    """
    Why: 强类型领域实体，拒绝裸字典 (Primitive Obsession) 传递，确保元数据内存布局确定性。
    """
    name: str
    func: Any  # Can be a Callable or a Toolkit instance
    description: str
    roles: Set[str] = field(default_factory=set)

    def to_schema(self) -> Dict[str, Any]:
        """Why: 动态反射生成 Schema，解耦底层 LLM 规范要求。"""
        if not callable(self.func):
            # If it's a Toolkit, we might not need to parse schema here, or we can just return a placeholder
            return {
                "type": "toolkit",
                "name": self.name,
                "description": self.description
            }

        sig = inspect.signature(self.func)
        properties = {}
        required = []

        for param_name, param in sig.parameters.items():
            if param_name in ("self", "cls", "kwargs", "args"):
                continue

            param_type = "string"
            if param.annotation is int:
                param_type = "integer"
            elif param.annotation is float:
                param_type = "number"
            elif param.annotation is bool:
                param_type = "boolean"
            elif param.annotation is list or param.annotation is List:
                param_type = "array"

            properties[param_name] = {
                "type": param_type,
                "description": f"Parameter {param_name}",
            }
            if param.default is inspect.Parameter.empty:
                required.append(param_name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }


class DefaultToolRegistry:
    """
    Why: 隔离底层引擎对工具实例的调用假设，提供基于 Role 的上下文防污染路由。
    """

    def __init__(self, db: Optional[Any] = None):
        # Why: 预留 DB 但不强耦合，保障核心注册表的单元测试隔离性。
        self.db = db
        self._tools: Dict[str, ToolDefinition] = {}

    def register_tool(
        self,
        name: str,
        func: Any,
        description: str,
        roles: Optional[List[str]] = None,
    ) -> None:
        """Why: 支持 Role 绑定，实现细粒度的工具分配 (RBAC)，控制上下文爆炸。"""
        self._tools[name] = ToolDefinition(
            name=name,
            func=func,
            description=description,
            roles=set(roles) if roles else set(),
        )
        logger.debug(f"Tool registered: {name} (Roles: {roles or 'ALL'})")

    def get_tool(self, name: str) -> Optional[Any]:
        tool_def = self._tools.get(name)
        return tool_def.func if tool_def else None

    def get_all_tools(self) -> List[Any]:
        return [t.func for t in self._tools.values()]

    def build_from_hint(self, role: str) -> List[Any]:
        """Why: 按角色动态裁剪工具集，避免大模型 Context Window Pollution。"""
        if not role:
            return self.get_all_tools()

        role = role.lower()
        matched = []
        for t in self._tools.values():
            if not t.roles or role in [r.lower() for r in t.roles]:
                matched.append(t.func)

        return matched if matched else self.get_all_tools()

    def get_all_tool_schemas(self) -> List[Dict[str, Any]]:
        return [t.to_schema() for t in self._tools.values()]
