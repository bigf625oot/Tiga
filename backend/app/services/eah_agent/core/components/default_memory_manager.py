import logging
from typing import List, Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.llm_model import LLMModel
from app.services.eah_agent.storage.session_history import SessionHistory
from app.core.context_compressor import ContextCompressor
from app.schemas.system_config import ContextMemoryConfig
from app.crud.crud_system_config import system_config as crud_system_config

logger = logging.getLogger("eah.components.memory")

class DefaultMemoryManager:
    """
    默认的 MemoryManager 实现。
    整合了 SessionHistory (PostgreSQL), ContextCompressor, 和 LightRAG 的图谱记忆。
    """

    def __init__(self, db: AsyncSession, llm_model: Optional[LLMModel] = None):
        self.db = db
        self.llm_model = llm_model
        self._system_context_memory: Optional[ContextMemoryConfig] = None

    async def _get_system_context_memory(self) -> ContextMemoryConfig:
        if self._system_context_memory is not None:
            return self._system_context_memory

        row = await crud_system_config.get_by_key(self.db, "context-memory")
        if not row or not row.value:
            self._system_context_memory = ContextMemoryConfig()
            return self._system_context_memory

        try:
            self._system_context_memory = ContextMemoryConfig.model_validate(row.value)
        except Exception as e:
            logger.warning(f"Invalid system config context-memory: {e}")
            self._system_context_memory = ContextMemoryConfig()

        return self._system_context_memory

    async def add_message(self, session_id: str, role: str, content: str, **kwargs) -> None:
        history = SessionHistory(self.db)
        await history.add_message(session_id, role, content, **kwargs)

    async def get_messages(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        if limit is None:
            cfg = await self._get_system_context_memory()
            limit = cfg.context.history_limit
            
        history = SessionHistory(self.db)
        msgs = await history.get_messages(session_id, limit=limit)
        return [{"role": m.role, "content": m.content} for m in msgs]

    async def get_compressed_context(self, session_id: str, current_query: str) -> List[Dict[str, Any]]:
        try:
            cfg = await self._get_system_context_memory()
            history = SessionHistory(self.db)
            
            limit = cfg.context.history_limit
            threshold = cfg.context.compression_threshold
            enable_graph_memory = getattr(cfg.context, "enable_graph_memory", False)

            msgs = await history.get_messages(session_id, limit=limit)
            raw_history = [{"role": m.role, "content": m.content} for m in msgs]

            graph_memory_text = ""
            if enable_graph_memory and current_query:
                try:
                    from app.services.rag.retrieval.engines.lightrag import lightrag_engine
                    await lightrag_engine.ensure_initialized(self.db)
                    
                    memory_subgraph = lightrag_engine.query_subgraph(current_query, top_k=5)
                    if memory_subgraph and memory_subgraph.get("nodes"):
                        nodes = memory_subgraph.get("nodes", {})
                        node_desc = []
                        if isinstance(nodes, dict):
                            for k, v in nodes.items():
                                if isinstance(v, dict) and "description" in v:
                                    node_desc.append(f"- {v.get('name', k)}: {v['description']}")
                                elif isinstance(v, dict):
                                    node_desc.append(f"- {v.get('name', k)}")
                                else:
                                    node_desc.append(f"- {k}")
                        elif isinstance(nodes, list):
                             for n in nodes:
                                 if isinstance(n, dict):
                                      node_desc.append(f"- {n.get('name', n.get('id', 'Unknown'))}: {n.get('description', '')}")
                        
                        if node_desc:
                             graph_memory_text = "从历史中召回的相关记忆实体：\n" + "\n".join(node_desc[:10])
                except Exception as e:
                    logger.error(f"Failed to load graph memory: {e}")

            compressor = ContextCompressor(model=self.llm_model)
            compressed = await compressor.compress_context(raw_history, max_tokens=threshold)
            
            if graph_memory_text:
                compressed.insert(0, {
                    "role": "system",
                    "content": f"【系统提示：长期图谱记忆】\n{graph_memory_text}"
                })
            
            return compressed
            
        except Exception as e:
            logger.error(f"Failed to load and compress history: {e}")
            return []
