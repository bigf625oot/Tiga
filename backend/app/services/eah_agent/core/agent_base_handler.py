import logging
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, Optional, TypedDict, Literal, List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.llm_model import LLMModel
from app.services.eah_agent.core.agent_nlu import IntentResult
from app.schemas.system_config import ContextMemoryConfig
from app.crud.crud_system_config import system_config as crud_system_config
from app.services.eah_agent.storage.session_history import SessionHistory
from app.core.context_compressor import ContextCompressor

# 定义统一的输出类型，增强代码提示和健壮性
class StreamResponse(TypedDict):
    type: Literal["content", "think", "status", "error", "tool_start", "tool_end", "run_output"]
    content: Optional[Any]
    data: Optional[Any]

class BaseHandler(ABC):
    """
    Abstract base class for all agent handlers (Quick, Plan, Team, Flow).
    核心功能：
    1. 定义统一的处理接口（process方法）。
    2. 支持不同的LLM模型。
    3. 提供基础的日志记录功能。
    4. 提供通用的系统配置和历史记录获取能力。
    """

    def __init__(self, llm_model: Optional[LLMModel] = None):
        self.llm_model = llm_model
        # 自动获取子类的名称作为日志标识
        self.logger = logging.getLogger(self.__class__.__name__)
        self._system_context_memory: Optional[ContextMemoryConfig] = None
        self._db_for_system_config: Optional[AsyncSession] = None

    async def _get_system_context_memory(self, db: Optional[AsyncSession]) -> ContextMemoryConfig:
        if self._system_context_memory is not None:
            return self._system_context_memory

        if not db:
            self._system_context_memory = ContextMemoryConfig()
            return self._system_context_memory

        row = await crud_system_config.get_by_key(db, "context-memory")
        if not row or not row.value:
            self._system_context_memory = ContextMemoryConfig()
            return self._system_context_memory

        try:
            self._system_context_memory = ContextMemoryConfig.model_validate(row.value)
        except Exception as e:
            self.logger.warning(f"Invalid system config context-memory: {e}")
            self._system_context_memory = ContextMemoryConfig()

        return self._system_context_memory

    async def _get_history_messages_with_graph(self, db: Optional[AsyncSession], session_id: Optional[str], current_query: str = "") -> Tuple[List[Dict], bool]:
        """获取并压缩历史消息，融入图谱记忆。通用于各 Handler。"""
        if not db or not session_id:
            return [], False
        
        try:
            self._db_for_system_config = db
            cfg = await self._get_system_context_memory(db)
            history = SessionHistory(db)
            limit = cfg.context.history_limit
            threshold = cfg.context.compression_threshold
            enable_graph_memory = getattr(cfg.context, "enable_graph_memory", False)
            graph_hop_depth = getattr(cfg.context, "graph_hop_depth", 1)

            msgs = await history.get_messages(session_id, limit=limit)
            raw_history = [{"role": m.role, "content": m.content} for m in msgs]

            # 1. 尝试从 LightRAG 获取长期图谱记忆
            graph_memory_text = ""
            if enable_graph_memory and current_query:
                try:
                    from app.services.rag.retrieval.engines.lightrag import lightrag_engine
                    await lightrag_engine.ensure_initialized(db)
                    
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
                    self.logger.error(f"Failed to load graph memory: {e}")

            # 2. 如果不需要暴力压缩，直接插入图谱记忆
            compressor = ContextCompressor(model=self.llm_model)
            compressed = await compressor.compress_context(raw_history, max_tokens=threshold)
            
            if graph_memory_text:
                compressed.insert(0, {
                    "role": "system",
                    "content": f"【系统提示：长期图谱记忆】\n{graph_memory_text}"
                })
            
            return compressed, len(compressed) < len(raw_history)
        except Exception as e:
            self.logger.error(f"Failed to load history: {e}")
            return [], False

    @abstractmethod
    async def process(
        self, 
        input_text: str, 
        intent: IntentResult, 
        **kwargs
    ) -> AsyncGenerator[StreamResponse, None]:
        """
        Processes the user input based on the handler's logic.
        
        Args:
            input_text: 用户原始输入字符串
            intent: NLU 解析后的意图对象
            **kwargs: 额外参数（如 session_id, history, user_info 等）

        Yields:
            StreamResponse: 包含类型和内容的字典
        """
        # 在这里可以写一些通用的逻辑，或者直接 pass
        if False: yield  # 只是为了让编辑器知道这是一个生成器
        pass

    def _log_error(self, error: Exception):
        """通用的错误日志记录"""
        self.logger.error(f"Error processing request: {str(error)}", exc_info=True)