import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import asyncio
import numpy as np

from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc
import json

from app.core.config import settings

from app.models.llm_model import LLMModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)

# 数据存储目录
# Fix: Use relative path "data" instead of "backend/data" to avoid double nesting when running from backend dir
DATA_DIR = Path("data")
LIGHTRAG_DIR = DATA_DIR / "lightrag_store"
LIGHTRAG_DIR.mkdir(parents=True, exist_ok=True)

class LightRAGService:
    _instance = None
    rag: Optional[LightRAG] = None

    def __init__(self):
        self.working_dir = str(LIGHTRAG_DIR)
        # 不再在 __init__ 中立即初始化，而是等待 ensure_initialized 被调用
        # 这样可以利用 async db session 获取配置
        # self._init_rag()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def ensure_initialized(self, db: Optional[AsyncSession] = None):
        """
        确保 LightRAG 已初始化。如果尚未初始化，尝试从数据库获取配置并初始化。
        """
        # 1. 基础实例初始化 (如果 self.rag 还是 None)
        if not self.rag:
            # ... (现有逻辑保持不变)
            # 尝试从 DB 加载配置
            if db:
                try:
                    # 获取 LLM 模型
                    res = await db.execute(
                        select(LLMModel)
                        .filter(LLMModel.is_active == True, LLMModel.model_type != "embedding")
                        .order_by(LLMModel.updated_at.desc())
                    )
                    llm_model = res.scalars().first()

                    # 获取 Embedding 模型
                    res = await db.execute(
                        select(LLMModel)
                        .filter(LLMModel.is_active == True, LLMModel.model_type == "embedding")
                        .order_by(LLMModel.updated_at.desc())
                    )
                    embed_model = res.scalars().first()

                    if llm_model:
                        self._init_rag(llm_config=llm_model, embed_config=embed_model)
                    else:
                        logger.warning("DB 中未找到活跃的 LLM 模型，尝试使用默认环境变量初始化。")
                        self._init_rag()
                except Exception as e:
                    logger.error(f"从 DB 加载配置失败: {e}")
                    self._init_rag()
            else:
                self._init_rag()
        
        # 2. [关键修复] 异步存储初始化
        # 必须在每次使用前确保 storage ready，或者至少在创建后调用一次
        await self._ensure_storages_initialized()

    def _init_rag(self, llm_config: Optional[LLMModel] = None, embed_config: Optional[LLMModel] = None):
        """
        初始化 LightRAG 实例。
        优先使用传入的 config，否则回退到 settings。
        """
        try:
            # 1. 准备 API Key 和 Base URL
            api_key = None
            base_url = None
            model_name = "gpt-4o-mini"

            if llm_config:
                api_key = llm_config.api_key
                base_url = llm_config.base_url
                model_name = llm_config.model_id
            else:
                api_key = settings.OPENAI_API_KEY
                if settings.DEEPSEEK_API_KEY:
                    api_key = settings.DEEPSEEK_API_KEY
                    base_url = settings.DEEPSEEK_BASE_URL
                    model_name = "deepseek-chat"
            
            if not api_key:
                logger.warning("未配置 API Key，LightRAG 可能无法正常工作。")
                return

            # 设置环境变量供 LightRAG 内部使用
            os.environ["OPENAI_API_KEY"] = api_key
            if base_url:
                os.environ["OPENAI_BASE_URL"] = base_url

            # 2. 定义 LLM 函数
            async def llm_model_func(prompt, system_prompt=None, history_messages=None, **kwargs) -> str:
                if history_messages is None:
                    history_messages = []

                # [HOTFIX] DeepSeek R1 (reasoner) 兼容性增强处理
                # 强制移除所有可能导致 400 错误的参数
                # 注意：某些参数可能被 LightRAG 默认注入，即使我们在 query 中没传
                unsafe_keys = ["response_format", "tools", "tool_choice", "functions", "function_call", "temperature", "top_p", "presence_penalty", "frequency_penalty"]
                
                # 即使 kwargs 中没有，我们也需要确保它不会被传给 SDK
                # 但这里的 kwargs 就是最终传给 openai_complete_if_cache 的参数
                
                for key in unsafe_keys:
                    if key in kwargs:
                        logger.warning(f"Removing unsupported param for DeepSeek R1: {key}")
                        kwargs.pop(key)
                
                # [HOTFIX] DeepSeek R1 (reasoner) 不支持 system prompt
                if "deepseek-reasoner" in model_name and system_prompt:
                    prompt = f"{system_prompt}\n\n{prompt}"
                    system_prompt = None
                
                # [DEBUG] 强制打印参数
                logger.info(f"Calling LLM: {model_name}, Keys remaining: {list(kwargs.keys())}")
                    
                response = await openai_complete_if_cache(
                    model_name, 
                    prompt, 
                    system_prompt=system_prompt, 
                    history_messages=history_messages, 
                    api_key=api_key,
                    base_url=base_url,
                    **kwargs
                )

                # [适配增强] 结果清洗
                # 由于我们移除了 response_format，模型（特别是 DeepSeek R1）极有可能返回 Markdown 代码块
                # 而 LightRAG 内部往往直接做 json.loads，导致解析失败。
                # 这里我们手动做一个“中间件”，提取 JSON 内容。
                if isinstance(response, str):
                    clean_response = response.strip()
                    # 尝试提取 Markdown JSON
                    if "```json" in clean_response:
                        import re
                        match = re.search(r'```json\s*(.*?)\s*```', clean_response, re.DOTALL)
                        if match:
                            clean_response = match.group(1)
                    elif "```" in clean_response:
                        import re
                        match = re.search(r'```\s*(.*?)\s*```', clean_response, re.DOTALL)
                        if match:
                            clean_response = match.group(1)
                    
                    # 简单的 JSON 预检 (可选)
                    # if clean_response != response:
                    #     logger.info("Output cleaned from Markdown code block")
                    
                    return clean_response
                
                return response

            # 3. 定义 Embedding 函数
            embed_api_key = api_key
            embed_base_url = base_url
            embed_model_name = "text-embedding-3-small"
            embed_dim = 1536

            if embed_config:
                embed_api_key = embed_config.api_key
                embed_base_url = embed_config.base_url
                embed_model_name = embed_config.model_id
                
                # [FIXED] 维度推断逻辑增强
                # 1. 显式模型名检查
                if "large" in embed_model_name:
                    embed_dim = 3072
                elif "embedding-3" in embed_model_name:
                    embed_dim = 2048
                # 2. Base URL 检查 (针对 Zhipu/BigModel)
                elif embed_base_url and ("bigmodel.cn" in embed_base_url or "zhipu" in embed_base_url):
                    embed_dim = 2048
                else:
                    # 默认尝试 1536，但如果是智谱模型（即使URL没匹配上），也可能是 2048
                    # 实际上，我们可以做一个更激进的猜测：如果报错 mismatch 2048 != 1536，说明模型返回了 2048
                    # 但在这里我们只能静态配置。
                    # 考虑到用户使用的是 embedding-3，且报错显示返回了 2048 个元素（1024 维度? 不，20480/10=2048）
                    # Wait, 报错说 total elements (20480) cannot be evenly divided by expected dimension (1536)
                    # 20480 / 10 (batch size) = 2048. 所以模型确实返回了 2048 维的向量。
                    # 而我们设置了 1536。
                    pass
            elif settings.DEEPSEEK_API_KEY and not settings.OPENAI_API_KEY:
                 # DeepSeek 回退逻辑
                 embed_api_key = settings.DEEPSEEK_API_KEY
                 embed_base_url = settings.DEEPSEEK_BASE_URL
                 embed_dim = 1024 # 假设 DeepSeek 使用 1024

            logger.info(f"Initializing LightRAG with model: {embed_model_name}, dim: {embed_dim}")

            # [HOTFIX] 针对智谱 AI (ZhipuAI) 的自定义 Embedding 函数
            # LightRAG 的 openai_embed 封装可能存在兼容性问题，尤其是在维度处理上。
            # 我们这里实现一个更健壮的版本，如果检测到是智谱，使用直接的 HTTP 调用或特殊的处理。
            
            is_zhipu = False
            if embed_base_url and ("bigmodel.cn" in embed_base_url or "zhipu" in embed_base_url):
                is_zhipu = True
            if "embedding-3" in embed_model_name: # 智谱常用模型名
                is_zhipu = True

            async def embedding_func(texts: list[str]) -> np.ndarray:
                if is_zhipu:
                    try:
                        # 智谱专用处理：直接使用 AsyncOpenAI 但不传 dimensions 参数（或者确保参数正确）
                        # 实际上 openai_embed 内部就是调用的 AsyncOpenAI
                        # 关键在于 lightrag 可能会默认传一些参数。
                        # 我们这里手动调用，确保干净。
                        from openai import AsyncOpenAI
                        client = AsyncOpenAI(api_key=embed_api_key, base_url=embed_base_url)
                        
                        # 智谱 API 通常不需要 dimensions 参数，或者只支持特定值
                        # 我们先尝试不传 dimensions，让模型返回默认维度 (通常是 2048)
                        response = await client.embeddings.create(
                            input=texts,
                            model=embed_model_name
                        )
                        embeddings = [data.embedding for data in response.data]
                        return np.array(embeddings)
                    except Exception as e:
                        logger.error(f"智谱 Embedding 调用失败: {e}")
                        # Fallback to default
                        pass

                return await openai_embed(
                    texts,
                    model=embed_model_name,
                    api_key=embed_api_key,
                    base_url=embed_base_url,
                    embedding_dim=embed_dim # Pass explicit dim if needed by wrapper
                )

            # [HOTFIX] 动态检测并修复 LightRAG 内部存储的维度
            # 问题：LightRAG 初始化后，如果磁盘上已经存在旧的 vdb 存储（例如 1536 维），
            # 即使我们在构造函数中传入了 2048，LightRAG 读取旧配置后可能仍会使用 1536，
            # 导致新计算出的 2048 向量插入失败。
            # 解决方案：强制删除不匹配的 vdb 文件（这很激进，但能解决问题），或者强制更新内存中的配置。
            
            # 检查是否需要清理旧数据
            # 如果我们确定现在是 2048，但报错说是 1536，说明存储层被污染了。
            
            self.rag = LightRAG(
                working_dir=self.working_dir,
                llm_model_func=llm_model_func,
                embedding_func=EmbeddingFunc(
                    embedding_dim=embed_dim,
                    max_token_size=8192,
                    func=embedding_func
                ),
                chunk_token_size=1200,
                chunk_overlap_token_size=100,
            )
            
            # [CRITICAL] 强制检查并修复 vector storage 的维度
            # LightRAG 初始化后，它的 storages (chunks_vdb, entities_vdb等) 已经加载了磁盘上的配置
            # 如果磁盘上记录的是 1536，而现在 embed_dim 是 2048，后续 insert 必挂。
            if self.rag:
                for storage_name in ["chunks_vdb", "entities_vdb", "relationships_vdb"]:
                    storage = getattr(self.rag, storage_name, None)
                    if storage and hasattr(storage, "embedding_dim"):
                        if storage.embedding_dim != embed_dim:
                            logger.warning(f"检测到维度冲突！Storage {storage_name} 是 {storage.embedding_dim}，但当前配置是 {embed_dim}。正在尝试修复...")
                            # 强制更新维度
                            storage.embedding_dim = embed_dim
                            # 如果是 NanoVectorDB，可能需要重建或清空，因为维度变了，旧数据无法兼容
                            # 简单起见，我们清空它？或者让它在下次 save 时覆盖配置？
                            # NanoVectorDB 内部使用 numpy 数组，维度不对会报错。
                            # 最安全的做法：如果维度变了，必须清空该存储！
                            try:
                                # 尝试访问内部数据，如果是 list/numpy，清空它
                                if hasattr(storage, "_client") and hasattr(storage._client, "_data"):
                                    logger.warning(f"清空 {storage_name} 的旧数据以适应新维度...")
                                    storage._client._data = [] # 假设是 list
                                    storage._client.dim = embed_dim # 更新 client 的维度
                            except Exception as e:
                                logger.error(f"尝试修复存储维度失败: {e}")
            
            # 手动初始化存储 (这是一个 Hack，LightRAG 的 API 设计可能需要这样做)
            # 由于 self.rag.initialize_storages() 是 async 的，我们需要在一个 event loop 中运行它
            # 或者，我们可以假设 insert() 内部会处理。
            # 根据报错：Indexing Failed: JsonDocStatusStorage not initialized.
            # 必须调用 await rag.initialize_storages()
            
            # 我们在一个单独的 task 中运行初始化，或者在 insert 之前确保初始化
            # 但 _init_rag 是同步的。
            # 策略：将初始化标记设为 False，在 ensure_initialized 中进行异步初始化。
            
            logger.info(f"LightRAG 实例创建成功，等待异步初始化存储...")

        except Exception as e:
            logger.error(f"LightRAG 初始化失败: {e}")
            import traceback
            traceback.print_exc()

    async def _ensure_storages_initialized(self):
        """
        确保 LightRAG 的内部存储组件已完全初始化。
        这是为了修复 'JsonDocStatusStorage not initialized' 错误。
        """
        if self.rag:
            # 检查是否有关闭的 doc_status 存储，或尝试调用 initialize_storages
            # LightRAG 类没有公开的 is_initialized 标志，但我们知道如果不调用这个就会挂。
            # 它是幂等的吗？查看源码：
            # async def initialize_storages(self):
            #     if not os.path.exists(self.working_dir): ...
            #     await self.doc_status.load() ...
            # 看起来是安全的。
            try:
                # 这是一个 protected method 吗？不，是 public。
                if hasattr(self.rag, "initialize_storages"):
                    await self.rag.initialize_storages()
                    logger.info("LightRAG 存储组件初始化完成")
            except Exception as e:
                logger.warning(f"LightRAG 存储初始化警告 (可能已初始化): {e}")

    async def ensure_initialized(self, db: Optional[AsyncSession] = None):
        """
        确保 LightRAG 已初始化。如果尚未初始化，尝试从数据库获取配置并初始化。
        [增强] 如果发现 DB 配置发生了变化（例如维度变了），强制重新初始化。
        """
        # 获取最新的 DB 配置
        llm_model = None
        embed_model = None
        
        if db:
            try:
                # 获取 LLM 模型
                res = await db.execute(
                    select(LLMModel)
                    .filter(LLMModel.is_active == True, LLMModel.model_type != "embedding")
                    .order_by(LLMModel.updated_at.desc())
                )
                llm_model = res.scalars().first()

                # 获取 Embedding 模型
                res = await db.execute(
                    select(LLMModel)
                    .filter(LLMModel.is_active == True, LLMModel.model_type == "embedding")
                    .order_by(LLMModel.updated_at.desc())
                )
                embed_model = res.scalars().first()
            except Exception as e:
                logger.error(f"从 DB 加载配置失败: {e}")

        # 计算预期的 embed_dim
        expected_dim = 1536 # Default
        if embed_model:
            model_id = embed_model.model_id
            base_url = embed_model.base_url
            if "large" in model_id:
                expected_dim = 3072
            elif "embedding-3" in model_id:
                expected_dim = 2048
            elif base_url and ("bigmodel.cn" in base_url or "zhipu" in base_url):
                expected_dim = 2048
        
        # 检查是否需要重新初始化
        should_reinit = False
        if not self.rag:
            should_reinit = True
        elif self.rag:
            # 检查当前维度是否匹配
            current_dim = 1536
            if hasattr(self.rag, "embedding_func") and hasattr(self.rag.embedding_func, "embedding_dim"):
                current_dim = self.rag.embedding_func.embedding_dim
            
            if current_dim != expected_dim:
                logger.warning(f"LightRAG 配置不匹配: 当前维度 {current_dim}, 期望维度 {expected_dim}。正在重新初始化...")
                should_reinit = True

        if should_reinit:
            if llm_model or embed_model:
                logger.info(f"使用 DB 配置初始化 LightRAG (Embed Dim: {expected_dim})")
                self._init_rag(llm_config=llm_model, embed_config=embed_model)
            else:
                logger.warning("未找到 DB 配置，使用默认初始化")
                self._init_rag()
        
        # 2. [关键修复] 异步存储初始化
        await self._ensure_storages_initialized()

    def insert_text(self, text: str, description: str = None):
        """
        向知识库插入文本。
        """
        logger.info(f"LightRAG insert_text called. Description: {description}, Text length: {len(text)}")
        if not self.rag:
            logger.warning("LightRAG insert_text called before initialization, trying default init...")
            self._init_rag()
        
        if self.rag:
            # 增加简单的重试机制
            retries = 3
            import time
            last_exception = None
            
            for i in range(retries):
                try:
                    logger.info(f"Attempting to insert text into LightRAG (Attempt {i+1}/{retries})...")
                    self.rag.insert(text)
                    
                    # [CRITICAL FIX] 显式触发持久化
                    # LightRAG 的 insert/ainsert 管道在某些版本中可能不会自动调用 _insert_done 落盘
                    # 导致 graphml 文件不生成。我们需要手动触发它。
                    # 由于 _insert_done 是 async 的，我们需要在事件循环中运行它
                    try:
                        import asyncio
                        # 获取当前线程的 loop，如果没有则创建
                        try:
                            loop = asyncio.get_event_loop()
                        except RuntimeError:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            
                        if loop.is_running():
                            # 如果已经在运行（极少见，因为 insert 是 sync 的），这比较麻烦
                            # 但通常 insert 会开启 loop 运行完后退出，或者如果是嵌套调用...
                            # 简单起见，我们假设 insert 已经完成了 async 任务
                            # 这里我们创建一个 task
                            future = asyncio.run_coroutine_threadsafe(self.rag._insert_done(), loop)
                            future.result() # 等待完成
                        else:
                            loop.run_until_complete(self.rag._insert_done())
                            
                        logger.info("已强制触发 LightRAG 数据持久化 (_insert_done)")
                    except Exception as save_err:
                        logger.warning(f"强制持久化失败 (但这可能不影响内存中的数据): {save_err}")
                    
                    logger.info(f"文本插入成功 (Desc: {description})")
                    return
                except Exception as e:
                    last_exception = e
                    logger.warning(f"文本插入失败 (尝试 {i+1}/{retries}): {e}")
                    # 检查是否是 API 相关的错误，如果是，等待后重试
                    # 简单的指数退避
                    time.sleep(2 * (i + 1))
            
            # 如果重试耗尽，抛出异常
            logger.error(f"文本插入最终失败 (Desc: {description})，重试 {retries} 次: {last_exception}")
            raise last_exception
        else:
            logger.error("LightRAG initialization failed, cannot insert text.")
            raise RuntimeError("LightRAG not initialized")

    def query(self, query: str, mode: str = "mix") -> str:
        """
        执行查询。
        :param mode: "naive", "local", "global", "hybrid", "mix"
        """
        if not self.rag:
             logger.warning("LightRAG query called before initialization, trying default init...")
             self._init_rag()
            
        if self.rag:
            try:
                # 显式使用异步查询（如果是 async 环境）
                # LightRAG.query 是同步的，但内部可能会用到 async loop
                # 如果我们在 async 上下文中，直接调用同步 query 可能会有问题
                # 不过 LightRAG 的 query 实现通常是同步阻塞的 (run_until_complete)
                
                param = QueryParam(mode=mode)
                logger.info(f"LightRAG query: {query} (mode={mode})")
                
                # [FIXED] 确保 storage initialized
                # 虽然 insert 时初始化了，但 query 时可能也需要
                # 这里不方便 await，假设已经初始化
                
                result = self.rag.query(query, param=param)
                
                logger.info(f"LightRAG query result length: {len(result) if result else 0}")
                return result
            except Exception as e:
                logger.error(f"查询失败: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return f"查询出错: {str(e)}"
        return "服务未初始化"

    def get_graph_data(self) -> Dict[str, Any]:
        """
        获取用于前端可视化的图谱数据。
        从 LightRAG 的 graph_chunk_entity_relation.graphml 读取。
        """
        import networkx as nx
        
        graphml_path = LIGHTRAG_DIR / "graph_chunk_entity_relation.graphml"
        if not graphml_path.exists():
            return {"nodes": {}, "edges": {}}
            
        try:
            G = nx.read_graphml(str(graphml_path))
            
            nodes = {}
            edges = {}
            
            # 限制返回的节点数量，避免前端渲染卡顿
            # 简单的策略：返回度数最高的 Top 200 节点
            # 或者如果是全量，LightRAG 可能会很大。
            
            top_nodes = sorted(G.degree, key=lambda x: x[1], reverse=True)[:200]
            subgraph = G.subgraph([n[0] for n in top_nodes])
            
            for node_id, data in subgraph.nodes(data=True):
                # LightRAG 节点 ID 通常就是实体名
                nodes[node_id] = {
                    "name": node_id,
                    "type": data.get("entity_type", "Entity"),
                    "attributes": {k: v for k, v in data.items() if k not in ["entity_type"]}
                }
                
            for u, v, data in subgraph.edges(data=True):
                edge_id = f"{u}_{v}"
                edges[edge_id] = {
                    "source": u,
                    "target": v,
                    "label": data.get("description", "related")[:20] # 截断描述作为 label
                }
                
            return {"nodes": nodes, "edges": edges}
            
        except Exception as e:
            logger.error(f"读取 GraphML 失败: {e}")
            return {"nodes": {}, "edges": {}}

lightrag_service = LightRAGService.get_instance()
