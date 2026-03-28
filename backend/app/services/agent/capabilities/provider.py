from typing import Protocol, List, Any, Dict, Optional, runtime_checkable
from agno.tools import Toolkit

@runtime_checkable
class CapabilityProvider(Protocol):
    """
    统一所有外部能力的加载与调用
    不管是 MCP、本地函数、还是高级 Skill，统统收敛于此接口。
    """
    
    @property
    def provider_type(self) -> str:
        """返回能力提供者类型 (e.g., 'mcp', 'local', 'skill')"""
        ...
        
    async def get_tools(self) -> List[Toolkit]:
        """
        获取当前提供者支持的工具集
        返回的是 Agno 框架可直接消费的 Toolkit 实例列表
        """
        ...
        
    def get_system_prompt_snippet(self) -> Optional[str]:
        """
        部分能力(如 Skill)需要向 System Prompt 注入元指令
        """
        return None
