import logging
from typing import List, Dict, Any

from app.services.agent.tools.registry import discover_tools, get_tool_metadata

logger = logging.getLogger(__name__)

class ToolRetriever:
    """
    P10 Architecture: Tool Retriever (Tools RAG)
    职责: 维护全局可用工具的元数据索引，并提供基于语义或规则的高并发召回能力。
    这是消除大模型“工具集爆炸”和“上下文污染”的核心组件。
    """
    
    _instance = None
    _is_initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ToolRetriever, cls).__new__(cls)
            cls._instance._tool_index = []
        return cls._instance

    def initialize(self):
        """系统启动时预热，构建工具的内存倒排索引或语义树"""
        if self._is_initialized:
            return
            
        try:
            # 1. 扫描所有可用工具的元数据
            metadata_list = discover_tools(include_metadata=True)
            self._tool_index = metadata_list
            self._is_initialized = True
            logger.info(f"ToolRetriever initialized with {len(self._tool_index)} tools.")
        except Exception as e:
            logger.error(f"Failed to initialize ToolRetriever: {e}")

    async def retrieve(self, query: str, top_k: int = 3, paradigm: str = "lite") -> List[str]:
        """
        基于用户 query 动态召回最相关的 K 个工具。
        Trade-offs: 为了保证 NLU 的极致低延迟，第一版采用基于规则和 TF-IDF 的快速启发式召回。
        后续可无缝升级为基于 LanceDB 的密集向量检索 (Dense Retrieval)。
        """
        if not self._is_initialized:
            self.initialize()
            
        if not query or not self._tool_index:
            return self._get_fallback_tools(paradigm)

        query_lower = query.lower()
        scored_tools = []

        for meta in self._tool_index:
            # 跳过不可用工具
            if not getattr(meta, 'is_available', True):
                continue
                
            score = 0.0
            name = getattr(meta, 'name', '').lower()
            desc = getattr(meta, 'description', '').lower()
            
            # 简单粗暴的启发式计分 (Heuristic Scoring)
            # 1. 精确匹配名字
            if name in query_lower:
                score += 5.0
                
            # 2. 关键词匹配描述
            keywords = [w for w in query_lower.split() if len(w) > 1]
            for kw in keywords:
                if kw in desc:
                    score += 1.0
                    
            # 3. 领域特征加权
            if paradigm == "data_query" and "sql" in desc or "database" in desc:
                score += 2.0
            if paradigm == "agentic" and "file" in desc or "shell" in desc:
                score += 1.5

            if score > 0:
                scored_tools.append((meta.name, score))

        # 按分数降序，取 Top K
        scored_tools.sort(key=lambda x: x[1], reverse=True)
        suggested = [t[0] for t in scored_tools[:top_k]]
        
        # 如果启发式召回失败，走降级池
        if not suggested:
            return self._get_fallback_tools(paradigm)
            
        logger.info(f"Tools RAG recalled: {suggested} for query: '{query[:20]}...'")
        return suggested

    def _get_fallback_tools(self, paradigm: str) -> List[str]:
        """防御性降级策略：决不全量兜底，只给生存必需品"""
        if paradigm == "lite":
            return ["duckduckgo"]  # Lite 模式只给基础搜索
        elif paradigm == "agentic":
            return ["duckduckgo", "calculator"]  # 复杂任务给搜索和计算
        elif paradigm == "specialized":
            return ["data_toolkit"]
        return []

tool_retriever = ToolRetriever()
