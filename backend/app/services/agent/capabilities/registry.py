import logging
from typing import List, Dict, Type
from sqlalchemy.ext.asyncio import AsyncSession

from agno.tools import Toolkit
from .provider import CapabilityProvider

logger = logging.getLogger(__name__)

class CapabilityRegistry:
    """
    P10 级注册中心：解耦能力的装配与使用。
    使用策略模式管理不同的 CapabilityProvider。
    """
    
    def __init__(self):
        self._providers: List[CapabilityProvider] = []
        
    def register_provider(self, provider: CapabilityProvider):
        """动态注册能力提供者"""
        self._providers.append(provider)
        logger.debug(f"Registered capability provider: {provider.provider_type}")
        
    async def resolve_all_tools(self) -> List[Toolkit]:
        """
        并行解析所有 Provider 的工具，大幅提升加载性能。
        解决原来串行加载慢、异常处理混乱的问题。
        """
        import asyncio
        
        tools = []
        tasks = [provider.get_tools() for provider in self._providers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for provider, result in zip(self._providers, results):
            if isinstance(result, Exception):
                logger.error(f"Provider {provider.provider_type} failed to load tools: {result}", exc_info=True)
            else:
                tools.extend(result)
                
        return tools

    def get_prompt_snippets(self) -> List[str]:
        """提取所有需要注入的指令"""
        snippets = []
        for p in self._providers:
            snippet = p.get_system_prompt_snippet()
            if snippet:
                snippets.append(snippet)
        return snippets
