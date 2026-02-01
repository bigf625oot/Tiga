import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import asyncio
import numpy as np
import time

from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import openai_embed
from lightrag.utils import EmbeddingFunc
import json
from openai import OpenAI, AsyncOpenAI

from app.core.config import settings

from app.models.llm_model import LLMModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pathlib import Path
from app.models.knowledge import KnowledgeDocument
from app.services.oss_service import oss_service
from app.services.document_parser import parse_local_file

logger = logging.getLogger(__name__)

# 数据存储目录
# Fix: Use relative path "data" instead of "backend/data" to avoid double nesting when running from backend dir
DATA_DIR = Path("data")
LIGHTRAG_DIR = DATA_DIR / "lightrag_store"
LIGHTRAG_DIR.mkdir(parents=True, exist_ok=True)

class LightRAGService:
    _instance = None
    rag: Optional[LightRAG] = None
    _trans_cache: Dict[str, str] = {}
    _runtime_vars: Dict[str, Any] | None = None
    _last_context: Dict[str, Any] | None = None
    _dim_meta_file: Path = LIGHTRAG_DIR / "vector_dim.meta"
    _chunks_cache: Dict[str, str] = {}
    _chunks_mtime: float = 0

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
            # 仅允许使用数据库激活的模型进行初始化
            if not db:
                raise RuntimeError("LightRAG 初始化需要数据库会话以读取激活模型")
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

                if not llm_model or not embed_model:
                    raise RuntimeError("未找到激活的 LLM 或嵌入模型，无法初始化 LightRAG")

                self._init_rag(llm_config=llm_model, embed_config=embed_model)
            except Exception as e:
                logger.error(f"从 DB 加载配置失败: {e}")
                raise
        
        # 2. [关键修复] 异步存储初始化
        # 必须在每次使用前确保 storage ready，或者至少在创建后调用一次
        await self._ensure_storages_initialized()

    def _init_rag(self, llm_config: Optional[LLMModel] = None, embed_config: Optional[LLMModel] = None):
        """
        初始化 LightRAG 实例。
        优先使用传入的 config，否则回退到 settings。
        """
        try:
            # 强制要求来自数据库的激活模型
            if not llm_config or not embed_config:
                logger.error("缺少激活的 LLM 或嵌入模型配置，LightRAG 初始化被拒绝")
                return
            
            self._llm_config = llm_config
            self._embed_config = embed_config

            # 1. 准备 API Key 和 Base URL
            api_key = None
            base_url = None
            model_name = "gpt-4o-mini"

            api_key = llm_config.api_key
            base_url = llm_config.base_url
            model_name = llm_config.model_id
            
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
                
                # [Optimization] Capture retrieval context from LightRAG system prompt
                if system_prompt and "---Context---" in system_prompt:
                    try:
                        self._last_context = {"raw": system_prompt.split("---Context---")[-1]}
                        # 尝试提取具体的实体和 Chunk 列表以供 UI 展示
                        if "Reference Document List" in system_prompt:
                            ref_list_part = system_prompt.split("Reference Document List")[-1].split("---")[0]
                            self._last_context["chunks"] = ref_list_part.strip()
                        if "Knowledge Graph Data (Entity)" in system_prompt:
                            kg_part = system_prompt.split("Knowledge Graph Data (Entity)")[-1].split("```json")[-1].split("```")[0]
                            self._last_context["entities"] = kg_part.strip()
                    except Exception:
                        pass

                # [Feature] Dynamic Retrieval Scope Filtering
                # If filter_doc_id is set, we strip out any context not belonging to that doc.
                try:
                    rv = getattr(self, "_runtime_vars", None)
                    filter_doc_id = (rv or {}).get("filter_doc_id")
                    if filter_doc_id and system_prompt and "---Context---" in system_prompt:
                        import re
                        marker = f"doc#{filter_doc_id}"
                        parts = system_prompt.split("---Context---")
                        base_prompt = parts[0]
                        context_part = parts[1]
                        
                        # 1. Filter Chunks in "Reference Document List"
                        # Each chunk starts with [n]
                        if "Reference Document List" in context_part:
                            chunk_sections = re.split(r"(\[\d+\])", context_part)
                            # chunk_sections[0] is everything before the first [n]
                            new_context = chunk_sections[0]
                            for i in range(1, len(chunk_sections), 2):
                                marker_tag = chunk_sections[i]
                                chunk_body = chunk_sections[i+1]
                                # Check if this chunk belongs to our doc
                                if marker in chunk_body:
                                    new_context += marker_tag + chunk_body
                            context_part = new_context

                        # 2. Filter Entities in "Knowledge Graph Data (Entity)"
                        if "Knowledge Graph Data (Entity)" in context_part:
                            try:
                                # Extract the JSON block
                                kg_match = re.search(r"(####### Knowledge Graph Data \(Entity\)\s+```json\s+)([\s\S]*?)(\s+```)", context_part)
                                if kg_match:
                                    prefix = kg_match.group(1)
                                    json_str = kg_match.group(2)
                                    suffix = kg_match.group(3)
                                    
                                    entities = json.loads(json_str)
                                    if isinstance(entities, list):
                                        # Keep entities if source_id contains our marker
                                        filtered_entities = [
                                            ent for ent in entities 
                                            if marker in str(ent.get("source_id", "")) or marker in str(ent.get("SOURCE_ID", ""))
                                        ]
                                        new_kg_json = json.dumps(filtered_entities, ensure_ascii=False, indent=2)
                                        context_part = context_part.replace(json_str, new_kg_json)
                            except Exception as e:
                                logger.warning(f"Failed to filter entities in context: {e}")
                                
                        system_prompt = base_prompt + "---Context---\n" + context_part
                        # [Refinement] Add a strict document scope reminder
                        system_prompt += f"\n\n注意：你当前处于“当前文档”检索模式，必须仅基于 doc#{filter_doc_id} 的内容回答，严禁引用其他文档或你的预训练知识。"
                        logger.info(f"Filtered context to doc#{filter_doc_id}")
                except Exception as e:
                    logger.error(f"Context filtering failed: {e}")

                try:
                    from app.core.config import settings as _s
                    if not system_prompt:
                        fp = getattr(_s, "QA_SYSTEM_PROMPT_FILE", "backend/prompts/qa_system.md")
                        p = Path(fp)
                        if p.exists():
                            system_prompt = p.read_text(encoding="utf-8").strip()
                        else:
                            system_prompt = getattr(_s, "QA_SYSTEM_PROMPT", None)
                except Exception:
                    pass
                # 变量注入
                try:
                    from datetime import datetime
                    now = datetime.now().strftime("%Y-%m-%d")
                    rv = getattr(self, "_runtime_vars", None)
                    kv = (rv or {}).get("knowledge", "")
                    hist = (rv or {}).get("history", "")
                    if kv and len(kv) > 6000:
                        kv = kv[:6000]
                    if hist and len(hist) > 2000:
                        hist = hist[:2000]
                    if system_prompt:
                        system_prompt = system_prompt.replace("{current_date}", now).replace("{knowledge}", kv).replace("{history}", hist)
                except Exception:
                    pass
                # 构造消息并使用用户配置的 LLMModel（基于 base_url 的 OpenAI 兼容接口）
                try:
                    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
                    messages = []
                    if "deepseek-reasoner" in model_name and system_prompt:
                        # R1 不支持 system role：将系统提示拼接到用户内容
                        messages.append({"role": "user", "content": f"{system_prompt}\n\n{prompt}"})
                    else:
                        if system_prompt:
                            messages.append({"role": "system", "content": system_prompt})
                        messages.append({"role": "user", "content": prompt})
                    # 不传 response_format / tools 等不兼容参数
                    logger.info(f"Calling LLM: {model_name} via base_url={base_url or 'default'}")
                    resp = await client.chat.completions.create(model=model_name, messages=messages, temperature=0)
                    response = resp.choices[0].message.content if (resp and resp.choices) else ""
                except Exception as e:
                    logger.error(f"LLM 调用失败: {e}")
                    response = ""

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
            embed_api_key = embed_config.api_key
            embed_base_url = embed_config.base_url
            embed_model_name = embed_config.model_id
            embed_dim = 1536
            if "text-embedding-v4" in embed_model_name:
                embed_dim = 1024
            elif "large" in embed_model_name:
                embed_dim = 3072
            elif "embedding-3" in embed_model_name:
                embed_dim = 2048
            # 自动探测实际维度（优先保障兼容）
            try:
                probe_client = OpenAI(api_key=embed_api_key, base_url=embed_base_url) if embed_base_url else OpenAI(api_key=embed_api_key)
                probe_resp = probe_client.embeddings.create(input=["dim_probe"], model=embed_model_name)
                actual = len(probe_resp.data[0].embedding) if (probe_resp and probe_resp.data) else None
                if actual and actual > 0:
                    embed_dim = actual
                    logger.info(f"Auto-detected embedding dim: {actual} for {embed_model_name}")
            except Exception as _e:
                logger.warning(f"Auto-detect embed dim failed, use heuristic {embed_dim}: {_e}")

            logger.info(f"Initializing LightRAG with model: {embed_model_name}, dim: {embed_dim}")

            async def embedding_func(texts: list[str]) -> np.ndarray:
                from openai import AsyncOpenAI
                client = AsyncOpenAI(api_key=embed_api_key, base_url=embed_base_url)
                resp = await client.embeddings.create(model=embed_model_name, input=texts)
                arr = np.array([d.embedding for d in resp.data], dtype=float)
                try:
                    if isinstance(arr, np.ndarray):
                        out = arr
                    else:
                        out = np.array(arr, dtype=float)
                    actual_dim = out.shape[1] if out.ndim == 2 else embed_dim
                    if actual_dim > embed_dim:
                        out = out[:, :embed_dim]
                    elif actual_dim < embed_dim:
                        pad = np.zeros((out.shape[0], embed_dim - actual_dim), dtype=float)
                        out = np.concatenate([out, pad], axis=1)
                    if out.shape[0] < len(texts):
                        pad_rows = np.zeros((len(texts) - out.shape[0], embed_dim), dtype=float)
                        out = np.concatenate([out, pad_rows], axis=0)
                    elif out.shape[0] > len(texts):
                        out = out[:len(texts), :]
                    return out
                except Exception as e:
                    logger.error(f"Embedding output normalization failed: {e}")
                    return np.zeros((len(texts), embed_dim), dtype=float)

            # [CRITICAL HOTFIX] 统一覆盖 LightRAG 内部的 openai_embed，避免 1536 固定维度假设
            try:
                import lightrag.llm.openai as _lo
                def _patched_openai_embed(texts, model, api_key=None, base_url=None, embedding_dim=None):
                    from openai import OpenAI
                    client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
                    resp = client.embeddings.create(model=model, input=texts)
                    emb = [d.embedding for d in resp.data]
                    return np.array(emb)
                _lo.openai_embed = _patched_openai_embed
                logger.info("Patched lightrag.llm.openai.openai_embed to dynamic dimension")
            except Exception as e:
                logger.warning(f"Failed to patch openai_embed: {e}")

            # [HOTFIX] 动态检测并修复 LightRAG 内部存储的维度
            # 问题：LightRAG 初始化后，如果磁盘上已经存在旧的 vdb 存储（例如 1536 维），
            # 即使我们在构造函数中传入了 2048，LightRAG 读取旧配置后可能仍会使用 1536，
            # 导致新计算出的 2048 向量插入失败。
            # 解决方案：强制删除不匹配的 vdb 文件（这很激进，但能解决问题），或者强制更新内存中的配置。
            
            # 检查是否需要清理旧数据
            # 如果我们确定现在是 2048，但报错说是 1536，说明存储层被污染了。
            
            # [HOTFIX] 强制覆盖 LightRAG 内部 Prompt 为中文优化版并增强引用逻辑
            try:
                import lightrag.prompt as _lp
                
                # 1. 增强系统提示词，特别强调翻译实体为中文，并包含文档实体提取逻辑
                _lp.PROMPTS["entity_extraction_system_prompt"] = _lp.PROMPTS["entity_extraction_system_prompt"].replace(
                    "Retain proper nouns in their original language",
                    "Translate proper nouns and all entities to Chinese whenever possible to ensure a consistent Chinese Knowledge Graph"
                )
                # 显式添加中文指令，并要求提取“文档”作为核心实体
                if "Simplified Chinese" not in _lp.PROMPTS["entity_extraction_system_prompt"]:
                    _lp.PROMPTS["entity_extraction_system_prompt"] += """

注意：
1. 请务必使用简体中文输出所有实体名称、类型和描述。
2. 即使原文是英文或其他语言，也请将其翻译为准确、专业的中文术语。
3. 实体描述应详细且完全使用中文。
4. **核心要求：始终将“源文档/文件”提取为一个独立的实体。**
   - 实体类型设为“文件”或“文档”。
   - 尽力从文本标题、页眉或正文中提取其真实名称（如“每日情报_AI与算力”）。
   - 提取文件中的日期信息、作者、来源等作为其实体描述的一部分。
   - **建立联系**：将文中提取的所有其他实体与该“文档”实体建立联系（如“提及于”、“来源自”）。
5. 保持术语的一致性。
"""

                # 2. 增强 RAG 响应提示词，强制要求正文引用 (In-text citations)，并严禁末尾引用区
                _lp.PROMPTS["rag_response"] = _lp.PROMPTS["rag_response"].replace(
                    "Track the reference_id of the document chunk which directly support the facts presented in the response.",
                    "Track the reference_id of the document chunk and the names of entities which directly support the facts presented in the response."
                ).replace(
                    "Generate a references section at the end of the response.",
                    "Generate in-text citations using [[Source: n]] for chunks and [[Entity: Name]] for entities. DO NOT generate a references section at the end of the response."
                )
                
                # 显式要求引用格式
                if "正文引用" not in _lp.PROMPTS["rag_response"]:
                    _lp.PROMPTS["rag_response"] = _lp.PROMPTS["rag_response"].replace(
                        "---Instructions---",
                        """---Instructions---

0. 强制引用规则：
  - **正文引用**：在回答的每一段话中，必须在所引用的事实后方标注来源。
  - **Chunk 引用**：使用 `[[Source: n]]` 格式（例如：事实内容[[Source: 1]]），其中 n 对应 `Reference Document List` 中的 ID。
  - **实体引用**：当提到知识图谱中的核心实体时，使用 `[[Entity: 实体名]]` 格式（例如：[[Entity: 电能计量]]）。
  - **严禁仅在结尾列出引用**，必须在正文事实发生处即时标注。
  - **严禁生成末尾引用区**：严禁在回答末尾输出任何形式的 'References'、'Sources'、'参考来源'、'引用列表' 或对应的列表内容。"""
                    )

                logger.info("Enhanced LightRAG prompts for Chinese and In-text Citations")
            except Exception as e:
                logger.warning(f"Failed to enhance prompts: {e}")

            try:
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
                    addon_params={
                        "language": "Chinese",
                        "entity_types": ["人物", "组织", "地点", "事件", "概念", "方法", "技术", "物品", "其他"]
                    }
                )
            except AssertionError as ae:
                msg = str(ae)
                if "Embedding dim mismatch" in msg:
                    logger.warning(f"Detected vector store dim mismatch at init ({msg}), cleaning stores and retrying...")
                    self._clean_vector_stores()
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
                        addon_params={
                            "language": "Chinese",
                            "entity_types": ["人物", "组织", "地点", "事件", "概念", "方法", "技术", "物品", "其他"]
                        }
                    )
                else:
                    raise
            
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
                raise
        else:
            raise RuntimeError("LightRAG 初始化需要数据库会话以读取激活模型")

        if not llm_model or not embed_model:
            raise RuntimeError("未找到激活的 LLM 或嵌入模型，无法初始化 LightRAG")

        # 计算预期的 embed_dim
        expected_dim = 1536 # Default
        if embed_model:
            model_id = embed_model.model_id
            base_url = embed_model.base_url
            provider = getattr(embed_model, "provider", "") or ""
            if "large" in model_id:
                expected_dim = 3072
            elif "embedding-3" in model_id:
                expected_dim = 2048
            elif base_url and ("bigmodel.cn" in base_url or "zhipu" in base_url):
                expected_dim = 2048
            elif "text-embedding-v4" in model_id or provider.lower() == "aliyun":
                expected_dim = 1024
        # 如果历史维度与当前预期不一致，提前清理旧向量库，避免 NanoVectorDB 维度断言失败
        try:
            last_dim = None
            if self._dim_meta_file.exists():
                try:
                    last_dim = int(self._dim_meta_file.read_text().strip())
                except Exception:
                    last_dim = None
            if last_dim and expected_dim and last_dim != expected_dim:
                logger.warning(f"Detected embed dim change: last {last_dim} -> expected {expected_dim}, cleaning vector stores...")
                self._clean_vector_stores()
        except Exception as e:
            logger.warning(f"Pre-clean vector stores failed: {e}")
        
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
            logger.info(f"使用 DB 配置初始化 LightRAG (Embed Dim: {expected_dim})")
            self._init_rag(llm_config=llm_model, embed_config=embed_model)
            # 保存当前维度以供下次比较
            try:
                self._dim_meta_file.write_text(str(expected_dim))
            except Exception:
                pass
        
        # 2. [关键修复] 异步存储初始化
        await self._ensure_storages_initialized()

    def set_runtime_vars(self, knowledge: str = "", history: List[str] | None = None, filter_doc_id: int | None = None):
        self._runtime_vars = {
            "knowledge": knowledge or "",
            "history": "\n".join(history or []) if history else "",
            "filter_doc_id": filter_doc_id
        }

    def clear_runtime_vars(self):
        self._runtime_vars = None

    def get_last_context(self) -> Dict[str, Any] | None:
        return self._last_context

    def clear_last_context(self):
        self._last_context = None

    def insert_text(self, text: str, description: str = None):
        """
        向知识库插入文本。
        """
        logger.info(f"LightRAG insert_text called. Description: {description}, Text length: {len(text)}")
        if not self.rag:
            logger.warning("LightRAG insert_text called before initialization, trying default init...")
            self._init_rag()
        
        if self.rag:
            # [Optimization] Prepend filename/description to text to ensure entity extractor can see it
            # This helps in creating the "Document" entity with correct attributes.
            if description:
                text_with_meta = f"--- Document Metadata ---\nSource: {description}\n------------------------\n\n{text}"
            else:
                text_with_meta = text

            # 增加简单的重试机制
            retries = 3
            import time
            last_exception = None
            
            for i in range(retries):
                try:
                    logger.info(f"Attempting to insert text into LightRAG (Attempt {i+1}/{retries})...")
                    self.rag.insert(text_with_meta, file_paths=description if description else None)
                    
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

    async def insert_text_async(self, text: str, description: str = None):
        logger.info(f"LightRAG insert_text_async called. Description: {description}, Text length: {len(text)}")
        if not self.rag:
            raise RuntimeError("LightRAG not initialized")
        
        # [Optimization] Prepend filename/description to text
        if description:
            text_with_meta = f"--- Document Metadata ---\nSource: {description}\n------------------------\n\n{text}"
        else:
            text_with_meta = text

        retries = 3
        last_exception = None
        for i in range(retries):
            try:
                await self.rag.ainsert(text_with_meta, file_paths=description if description else None)
                try:
                    await self.rag._insert_done()
                except Exception:
                    pass
                logger.info(f"文本异步插入成功 (Desc: {description})")
                return
            except Exception as e:
                last_exception = e
                logger.warning(f"异步文本插入失败 (尝试 {i+1}/{retries}): {e}")
                import asyncio as _asyncio
                await _asyncio.sleep(2 * (i + 1))
        logger.error(f"文本异步插入最终失败 (Desc: {description})，重试 {retries} 次: {last_exception}")
        raise last_exception

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
                
                param = QueryParam(mode=mode, enable_rerank=getattr(settings, "RERANK_ENABLED", False))
                logger.info(f"LightRAG query: {query} (mode={mode}, rerank={getattr(settings, 'RERANK_ENABLED', False)})")
                
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

    async def query_async(self, query: str, mode: str = "mix", filter_doc_id: int | None = None) -> str:
        if not self.rag:
            return "服务未初始化"
        try:
            if filter_doc_id:
                # If we have a doc filter, we should try to bias the query 
                # to help LightRAG's internal retrieval find relevant chunks.
                query = f"Based on doc#{filter_doc_id}: {query}"
                # Use "local" mode for single document focus to avoid global hallucination/noise
                mode = "local"
            
            param = QueryParam(mode=mode, enable_rerank=getattr(settings, "RERANK_ENABLED", False))
            logger.info(f"LightRAG aquery: {query} (mode={mode}, filter_doc={filter_doc_id}, rerank={getattr(settings, 'RERANK_ENABLED', False)})")
            result = await self.rag.aquery(query, param=param)
            self.clear_runtime_vars()
            return result
        except Exception as e:
            logger.error(f"异步查询失败: {e}")
            return f"查询出错: {str(e)}"

    def _load_chunks_cache(self):
        chunks_path = LIGHTRAG_DIR / "kv_store_text_chunks.json"
        if not chunks_path.exists():
            return
        
        mtime = os.path.getmtime(str(chunks_path))
        if mtime > self._chunks_mtime:
            try:
                with open(chunks_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # LightRAG kv_store format is often { "key": { "content": "..." } }
                    new_cache = {}
                    for k, v in data.items():
                        if isinstance(v, dict) and "content" in v:
                            new_cache[k] = v["content"]
                        elif isinstance(v, str):
                            new_cache[k] = v
                    self._chunks_cache = new_cache
                    self._chunks_mtime = mtime
            except Exception as e:
                logger.warning(f"Failed to load chunks cache: {e}")

    def get_graph_data(self, doc: Optional[KnowledgeDocument] = None) -> Dict[str, Any]:
        import networkx as nx
        
        graphml_path = LIGHTRAG_DIR / "graph_chunk_entity_relation.graphml"
        if not graphml_path.exists():
            return {"nodes": {}, "edges": {}}
            
        try:
            ttl = 30
            try:
                from app.core.config import settings
                ttl = int(getattr(settings, "GRAPH_CACHE_TTL", 30) or 30)
            except Exception:
                pass
            
            # [Optimization] Disable automatic post-translation as it's extremely slow
            # We now rely on enhanced entity extraction prompt to get Chinese entities directly
            enable_translation = False
            try:
                from app.core.config import settings
                enable_translation = getattr(settings, "ENABLE_GRAPH_TRANSLATION", False)
            except Exception:
                pass

            lang = "en" # Default to original
            try:
                from app.core.config import settings
                lang = getattr(settings, "GRAPH_LANG", "en") or "en"
            except Exception:
                pass

            mtime = os.path.getmtime(str(graphml_path))
            now = time.time()
            # [Optimization] Force re-processing if logic changed (version 2)
            logic_version = 2
            meta = getattr(self, "_graph_cache_meta", None)
            cache = getattr(self, "_graph_cache", None)
            if meta and cache:
                if meta.get("mtime") == mtime and (now - meta.get("ts", 0)) < ttl and meta.get("lang") == lang and meta.get("doc_id") == (getattr(doc, "id", None) if doc else None) and meta.get("v") == logic_version:
                    return cache
            
            self._load_chunks_cache()
            G = nx.read_graphml(str(graphml_path))
            
            # Optional filter by document
            if doc:
                fname = (doc.filename or "").strip()
                oss_name = Path(doc.oss_key).name if getattr(doc, "oss_key", None) else ""
                marker = f"doc#{doc.id}" if getattr(doc, "id", None) else ""
                keep = set()
                for node_id, data in G.nodes(data=True):
                    attrs = data or {}
                    fp = str(attrs.get("file_path") or "")
                    sid = str(attrs.get("source_id") or "")
                    if (fname and fname in fp) or (oss_name and oss_name in fp) or (marker and marker in sid):
                        keep.add(node_id)
                G = G.subgraph(keep) if keep else nx.Graph()  # empty if none
            
            nodes = {}
            edges = {}
            
            # 限制返回的节点数量，避免前端渲染卡顿
            # 简单的策略：返回度数最高的 Top 200 节点
            # 或者如果是全量，LightRAG 可能会很大。
            
            pr = {}
            try:
                pr = nx.pagerank(G)
            except Exception:
                pr = {n: d for n, d in G.degree}
            top_nodes_ids = [n for n, _ in sorted(pr.items(), key=lambda x: x[1], reverse=True)[:200]]
            subgraph = G.subgraph(top_nodes_ids)
            
            from datetime import datetime
            for node_id, data in subgraph.nodes(data=True):
                # LightRAG 节点 ID 通常就是实体名
                attrs = {k: v for k, v in data.items() if k not in ["entity_type"]}
                
                # 1. Format created_at
                if "created_at" in attrs:
                    try:
                        ts = float(attrs["created_at"])
                        attrs["created_at"] = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
                    except Exception:
                        pass
                
                # 2. Resolve source_id to chunk content (Handle multiple IDs separated by <SEP>)
                # Case-insensitive check for source_id
                sid_raw = attrs.get("source_id") or attrs.get("SOURCE_ID")
                if sid_raw:
                    sids = [s.strip() for s in str(sid_raw).split("<SEP>") if s.strip()]
                    chunk_list = []
                    for s in sids:
                        chunk_item = {"id": s}
                        if s in self._chunks_cache:
                            chunk_item["content"] = self._chunks_cache[s]
                        chunk_list.append(chunk_item)
                    attrs["chunks"] = chunk_list
                
                # 3. Mark internal fields for frontend filtering (Case-insensitive)
                internal_patterns = ["entity_id", "file_path_raw", "source_id", "truncate", "chunk_id"]
                all_keys = list(attrs.keys())
                for k in all_keys:
                    if any(p == k.lower() for p in internal_patterns):
                        attrs[f"_{k}"] = attrs.pop(k)
                
                nodes[node_id] = {
                    "name": node_id,
                    "type": data.get("entity_type", "Entity"),
                    "attributes": attrs
                }
                
            for u, v, data in subgraph.edges(data=True):
                edge_id = f"{u}_{v}"
                edges[edge_id] = {
                    "source": u,
                    "target": v,
                    "label": data.get("description", "related")[:20] # 截断描述作为 label
                }
                
            try:
                # Only translate if explicitly enabled and language is zh
                if enable_translation and lang.lower() == "zh":
                    texts = set()
                    exclude_attr_keys = {"entity_id", "source_id", "file_path", "chunk_id", "id", "uuid"}
                    for n in nodes.values():
                        name = n.get("name") or ""
                        if name:
                            texts.add(name)
                        attrs = n.get("attributes") or {}
                        for k, v in attrs.items():
                            if isinstance(v, str) and k not in exclude_attr_keys:
                                if v:
                                    texts.add(v)
                    for e in edges.values():
                        label = e.get("label") or ""
                        if label:
                            texts.add(label)
                    to_translate = [t for t in texts if t not in self._trans_cache]
                    if to_translate:
                        mapping = self._translate_texts_zh(to_translate)
                        logger.info(f"Translated {len(mapping)} new texts to Chinese")
                        for k, v in mapping.items():
                            self._trans_cache[k] = v
                    for n in nodes.values():
                        name = n.get("name") or ""
                        if name:
                            n["name"] = self._trans_cache.get(name, name)
                        attrs = n.get("attributes") or {}
                        for k, v in list(attrs.items()):
                            if isinstance(v, str) and k not in exclude_attr_keys:
                                attrs[k] = self._trans_cache.get(v, v)
                    for e in edges.values():
                        label = e.get("label") or ""
                        if label:
                            e["label"] = self._trans_cache.get(label, label)
                else:
                    if lang.lower() == "zh":
                        logger.info("Post-translation is disabled. Relying on extraction prompt for Chinese.")
            except Exception as te:
                logger.warning(f"Optional translation failed: {te}")
            
            out = {"nodes": nodes, "edges": edges}
            self._graph_cache = out
            self._graph_cache_meta = {"mtime": mtime, "ts": now, "lang": lang, "doc_id": getattr(doc, "id", None) if doc else None, "v": 2}
            return out
            
        except Exception as e:
            logger.error(f"读取 GraphML 失败: {e}")
            return {"nodes": {}, "edges": {}}

    def _translate_texts_zh(self, texts: List[str]) -> Dict[str, str]:
        if not texts:
            return {}
        try:
            # 优先使用配置的 LLM
            llm = getattr(self, "_llm_config", None)
            api_key = llm.api_key if llm else (os.environ.get("OPENAI_API_KEY") or "")
            base_url = llm.base_url if llm else (os.environ.get("OPENAI_BASE_URL") or None)
            model = llm.model_id if llm else "gpt-4o-mini"

            if not api_key:
                return {t: t for t in texts}

            client = OpenAI(api_key=api_key, base_url=base_url)
            # 分批翻译，避免 Prompt 过长
            batch_size = 50
            results = {}
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i+batch_size]
                content = (
                    "你是一个专业翻译助手。请将以下知识图谱中的术语、短语或描述翻译为简体中文。\n"
                    "要求：\n"
                    "1. 输出一个标准的 JSON 对象，格式为：{\"原文\": \"中文翻译\"}\n"
                    "2. 保持专业术语准确，符合行业规范\n"
                    "3. 保持缩写、代码、ID 等非文字内容不变\n"
                    "4. 如果原文已经是中文，请保持不变\n"
                    "5. 实体名称应翻译为准确的中文学术或通用名称\n"
                    "6. 只输出 JSON 对象，不要包含任何解释或 Markdown 标记\n\n"
                    f"待翻译内容：{json.dumps(list(batch), ensure_ascii=False)}"
                )
                
                logger.info(f"Translating {len(batch)} items to Chinese using {model}")
                resp = client.chat.completions.create(
                    model=model, 
                    messages=[
                        {"role": "system", "content": "你是一个只输出 JSON 的翻译机器人。"},
                        {"role": "user", "content": content}
                    ], 
                    temperature=0,
                    response_format={"type": "json_object"} if ("gpt-4" in model or "gpt-3.5" in model or "deepseek" in model) else None
                )
                
                data = resp.choices[0].message.content if resp and resp.choices else "{}"
                
                # 增强的 JSON 提取逻辑
                try:
                    # 移除可能的 Markdown 标记
                    if "```json" in data:
                        data = data.split("```json")[1].split("```")[0].strip()
                    elif "```" in data:
                        data = data.split("```")[1].split("```")[0].strip()
                    
                    m = json.loads(data)
                    if isinstance(m, dict):
                        for k, v in m.items():
                            results[str(k)] = str(v)
                except Exception as e:
                    logger.warning(f"Batch translate JSON parse failed: {e}, attempting fuzzy match...")
                    # 尝试正则表达式提取 JSON 结构
                    import re
                    matches = re.findall(r'"([^"]+)":\s*"([^"]+)"', data)
                    for k, v in matches:
                        results[k] = v
                    if not matches:
                        logger.error(f"Fuzzy match also failed for data: {data[:200]}...")
            
            return results
        except Exception as e:
            logger.warning(f"Graph translate failed: {e}")
        return {t: t for t in texts}

    def _clean_vector_stores(self):
        try:
            removed = 0
            import shutil
            for p in LIGHTRAG_DIR.iterdir():
                # 保留图谱文件，其余全部清理
                if p.is_file() and p.suffix.lower() == ".graphml":
                    continue
                try:
                    if p.is_dir():
                        shutil.rmtree(p, ignore_errors=True)
                    else:
                        p.unlink()
                    removed += 1
                except Exception:
                    pass
            logger.info(f"Vector store full cleanup done (keep *.graphml), removed {removed} entries")
        except Exception as e:
            logger.warning(f"Vector store cleanup failed: {e}")

    async def reset_vector_store(self, db: AsyncSession):
        self._clean_vector_stores()
        try:
            if self._dim_meta_file.exists():
                self._dim_meta_file.unlink()
        except Exception:
            pass
        self.rag = None
        await self.ensure_initialized(db)

    def search_chunks(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if not self.rag:
            self._init_rag()
        if not self.rag:
            return []
        try:
            storage = getattr(self.rag, "chunks_vdb", None)
            if hasattr(storage, "search"):
                res = storage.search(query, top_k=top_k)
                items = []
                for r in res or []:
                    preview = ""
                    score = 0.0
                    try:
                        preview = (getattr(r, "text", None) or getattr(r, "content", None) or "")
                        score = float(getattr(r, "score", 0.0) or 0.0)
                    except Exception:
                        pass
                    items.append({"title": "", "url": None, "page": None, "score": score, "preview": (preview or "")[:200]})
                return items
        except Exception as e:
            logger.warning(f"LightRAG chunk search failed: {e}")
        return []

    async def rebuild_store(self, db: AsyncSession, exclude_filenames: Optional[List[str]] = None):
        await self.ensure_initialized(db)
        try:
            import shutil
            if os.path.exists(self.working_dir):
                shutil.rmtree(self.working_dir, ignore_errors=True)
            os.makedirs(self.working_dir, exist_ok=True)
            self.rag = None
            await self.ensure_initialized(db)
            res = await db.execute(select(KnowledgeDocument).order_by(KnowledgeDocument.created_at.asc()))
            docs = res.scalars().all()
            for d in docs:
                if exclude_filenames and d.filename and d.filename in exclude_filenames:
                    continue
                temp_path = None
                text = ""
                try:
                    if d.oss_key:
                        ext = os.path.splitext(d.filename or "")[1] or ".txt"
                        temp_name = f"temp_rebuild_{d.id}{ext}"
                        temp_path = Path(self.working_dir) / temp_name
                        oss_service.download_file(d.oss_key, str(temp_path))
                        text = parse_local_file(str(temp_path))
                    else:
                        from app.services.knowledge_base import UPLOAD_DIR
                        candidate = UPLOAD_DIR / (d.filename or "")
                        if candidate.exists():
                            text = parse_local_file(str(candidate))
                    if text:
                        self.insert_text(text, description=f"doc#{d.id}:{d.filename}")
                except Exception as e:
                    logger.warning(f"Rebuild insert failed for {d.id}: {e}")
                finally:
                    if temp_path and os.path.exists(temp_path):
                        try:
                            os.remove(temp_path)
                        except Exception:
                            pass
        except Exception as e:
            logger.error(f"LightRAG rebuild failed: {e}")

lightrag_service = LightRAGService.get_instance()
