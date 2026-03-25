import inspect
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger("eah.components.tools")


@dataclass(slots=True)
class ToolDefinition:
    """
    强类型领域实体，避免使用裸字典 (Primitive Obsession) 传递工具定义。
    """
    name: str
    func: Callable
    description: str
    roles: Set[str] = field(default_factory=set)

    def to_schema(self) -> Dict[str, Any]:
        """
        根据函数签名动态反射生成符合 LLM 规范的 Function Schema。
        """
        sig = inspect.signature(self.func)
        properties = {}
        required = []

        for param_name, param in sig.parameters.items():
            if param_name in ("self", "cls", "kwargs", "args"):
                continue

            param_type = "string"  # 默认降级为 string
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
    Tool Registry: 生产级工具注册中心
    - 提供按 Role 路由的策略 (build_from_hint)
    - 提供反射 Schema 生成机制
    - 抹平底层 ExecutionEngine 对工具实例的调用假设
    """

    def __init__(self, db: Optional[Any] = None):
        # 预留 db，但不强制强耦合 AsyncSession，便于单元测试与独立演进
        self.db = db
        self._tools: Dict[str, ToolDefinition] = {}

    def register_tool(
        self,
        name: str,
        func: Callable,
        description: str,
        roles: Optional[List[str]] = None,
    ) -> None:
        """
        注册工具。允许绑定特定角色 (Role)，以实现细粒度的工具分配 (RBAC for Tools)。
        """
        self._tools[name] = ToolDefinition(
            name=name,
            func=func,
            description=description,
            roles=set(roles) if roles else set(),
        )
        logger.debug(f"Tool registered: {name} (Roles: {roles or 'ALL'})")

    def get_tool(self, name: str) -> Optional[Callable]:
        """获取单个工具函数"""
        tool_def = self._tools.get(name)
        return tool_def.func if tool_def else None

    def get_all_tools(self) -> List[Callable]:
        """
        向 ExecutionEngine 暴露的接口：获取全部可用工具实例（函数指针）。
        """
        return [t.func for t in self._tools.values()]

    def build_from_hint(self, role: str) -> List[Callable]:
        """
        向 ExecutionEngine 暴露的接口：根据角色 (Role) 或 Hint 分配专属工具。
        Why: 防止大模型被过多无关工具干扰 (Context Window Pollution)。
        """
        if not role:
            return self.get_all_tools()

        role = role.lower()
        matched = []
        for t in self._tools.values():
            # 如果工具未绑定任何角色（全局可用），或明确包含了请求的角色，则分发
            if not t.roles or role in [r.lower() for r in t.roles]:
                matched.append(t.func)

        return matched if matched else self.get_all_tools()

    def get_all_tool_schemas(self) -> List[Dict[str, Any]]:
        """
        返回当前注册表内所有工具的 OpenAPI Schema（基于 inspect 动态反射）。
        """
        return [t.to_schema() for t in self._tools.values()]
