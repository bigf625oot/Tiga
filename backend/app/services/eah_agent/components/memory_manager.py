import logging
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.llm_model import LLMModel
from app.services.eah_agent.storage.session_history import SessionHistory
from app.core.context_compressor import ContextCompressor
from app.schemas.system_config import ContextMemoryConfig
from app.crud.crud_system_config import system_config as crud_system_config

logger = logging.getLogger("eah.components.memory")

# =============================================================================
# Domain Entities 
# =============================================================================
@dataclass(slots=True)
class MemoryContextItem:
    """
    语义上下文的原子载体。
    Why: 拒绝使用裸 dict (Primitive Obsession)。通过 __slots__ 绑定内存布局，
    降低 Python 字典带来的内存碎片和 GC 压力（在大规模并发对话的上下文中尤为重要）。
    """
    role: str
    content: str

    def to_dict(self) -> Dict[str, Any]:
        return {"role": self.role, "content": self.content}


class SystemConfigCache:
    """
    配置热更新与防穿透层。
    Why: 避免高频会话调度时引发的 DB IO 瓶颈，利用时间窗口 (TTL) 换取极致的读取性能。
    Trade-offs: 容忍秒级的配置最终一致性，以换取零 IO 的内存级访问。
    """
    __slots__ = ('_config', '_last_fetch', 'ttl_seconds')

    def __init__(self, ttl_seconds: float = 60.0):
        self._config: Optional[ContextMemoryConfig] = None
        self._last_fetch: float = 0.0
        self.ttl_seconds = ttl_seconds

    def is_expired(self) -> bool:
        return self._config is None or (time.time() - self._last_fetch > self.ttl_seconds)

    def update(self, config: ContextMemoryConfig) -> None:
        self._config = config
        self._last_fetch = time.time()

    def get(self) -> Optional[ContextMemoryConfig]:
        return self._config


# =============================================================================
# Memory Strategies
# =============================================================================
class GraphMemoryRetriever:
    """
    长时图谱记忆召回策略。
    Why: 将异构存储 (Neo4j/Graph) 的召回逻辑从主流程中剥离，防止大段 if-else 污染主状态机。
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def recall(self, query: str) -> str:
        if not query:
            return ""
            
        try:
            # 延迟加载避免循环依赖，保持模块的拓扑单向性
            from app.services.knowledge.rag.retrieval.engines.lightrag import lightrag_engine
            await lightrag_engine.ensure_initialized(self.db)
            
            memory_subgraph = lightrag_engine.query_subgraph(query, top_k=5)
            nodes = memory_subgraph.get("nodes") if memory_subgraph else None
            
            if not nodes:
                return ""

            node_desc = self._parse_nodes(nodes)
            return "从历史中召回的相关记忆实体：\n" + "\n".join(node_desc[:10]) if node_desc else ""
            
        except Exception as e:
            logger.error(f"Failed to load graph memory: {e}")
            return ""

    def _parse_nodes(self, nodes: Any) -> List[str]:
        """多态解析：抹平不同图谱引擎返回的数据结构差异"""
        node_desc = []
        # 迭代器化处理，避免大集合时的内存逃逸
        iterable = nodes.items() if isinstance(nodes, dict) else ( (None, n) for n in nodes ) if isinstance(nodes, list) else []
        
        for k, v in iterable:
            if not isinstance(v, dict):
                node_desc.append(f"- {k or v}")
                continue
                
            name = v.get('name', v.get('id', k or 'Unknown'))
            desc = v.get('description', '')
            node_desc.append(f"- {name}: {desc}" if desc else f"- {name}")
            
        return node_desc


# =============================================================================
# Core Manager 
# =============================================================================
class DefaultMemoryManager:
    """
    Memory Manager
    职责：作为数据面的聚合根 (Aggregate Root)，协调短时记忆 (Session DB) 与长时记忆 (Graph) 的融合与压缩。
    """

    def __init__(self, db: AsyncSession, llm_model: Optional[LLMModel] = None):
        self.db = db
        self.llm_model = llm_model
        self._config_cache = SystemConfigCache(ttl_seconds=60.0)
        self._graph_retriever = GraphMemoryRetriever(db)

    async def _get_system_context_memory(self) -> ContextMemoryConfig:
        if not self._config_cache.is_expired():
            config = self._config_cache.get()
            if config is not None:
                return config

        row = await crud_system_config.get_by_key(self.db, "context-memory")
        config = ContextMemoryConfig()
        
        if row and row.value:
            try:
                config = ContextMemoryConfig.model_validate(row.value)
            except Exception as e:
                logger.warning(f"Invalid system config context-memory fallback to default: {e}")

        self._config_cache.update(config)
        return config

    async def add_message(self, session_id: str, role: str, content: str, **kwargs) -> None:
        """持久化短时记忆（当前依然强依赖 SessionHistory，未来可注入 StorageStrategy）"""
        history = SessionHistory(self.db)
        await history.add_message(session_id, role, content, **kwargs)

    async def get_messages(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取原始历史上下文。
        Why: 对外暴露 List[Dict] 以兼容现有生态，但内部流转建议采用强类型。
        """
        if limit is None:
            cfg = await self._get_system_context_memory()
            limit = cfg.context.history_limit
            
        history = SessionHistory(self.db)
        msgs = await history.get_messages(session_id, limit=limit)
        # 利用推导式和实体类，保证映射的确定性
        return [MemoryContextItem(role=m.role, content=m.content).to_dict() for m in msgs]

    async def get_compressed_context(self, session_id: str, current_query: str) -> List[Dict[str, Any]]:
        """
        全链路记忆装配：短时记忆 (DB) -> 长时记忆召回 (Graph) -> 密度压缩 (LLM) -> 最终上下文。
        """
        try:
            cfg = await self._get_system_context_memory()
            limit = cfg.context.history_limit
            threshold = cfg.context.compression_threshold
            enable_graph_memory = getattr(cfg.context, "enable_graph_memory", False)

            # 1. 提取短时记忆序列
            raw_history = await self.get_messages(session_id, limit=limit)

            # 2. 并行/异步召回长时记忆 (Graph RAG)
            graph_memory_text = ""
            if enable_graph_memory and current_query:
                graph_memory_text = await self._graph_retriever.recall(current_query)

            # 3. 语义密度压缩 (Token 阈值控制)
            compressor = ContextCompressor(model=self.llm_model)
            compressed = await compressor.compress_context(raw_history, max_tokens=threshold)
            
            # 4. 组装系统级长时提示词
            if graph_memory_text:
                compressed.insert(0, {
                    "role": "system",
                    "content": f"【系统提示：长期图谱记忆】\n{graph_memory_text}"
                })
            
            return compressed
            
        except Exception as e:
            logger.error(f"Failed to load and compress history: {e}")
            return []
