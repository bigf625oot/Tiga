import asyncio
import contextvars
import inspect
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from lightrag import LightRAG, QueryParam
from lightrag.utils import EmbeddingFunc
from openai import AsyncOpenAI, OpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.knowledge import KnowledgeDocument
from app.models.llm_model import LLMModel
from app.services.rag.parser import parse_local_file
from app.services.storage.service import storage_service

logger = logging.getLogger(__name__)

# ContextVars for request-scoped state
runtime_vars_ctx = contextvars.ContextVar("runtime_vars", default=None)
last_context_ctx = contextvars.ContextVar("last_context", default=None)

# 数据存储目录
# Fix: Use absolute path relative to backend directory to avoid CWD dependency
# Assuming this file is in app/services/rag/engines/
BACKEND_DIR = Path(__file__).resolve().parents[4] # engines -> rag -> services -> app -> backend
DATA_DIR = BACKEND_DIR / "data"
LIGHTRAG_DIR = DATA_DIR / "lightrag_store"
LIGHTRAG_DIR.mkdir(parents=True, exist_ok=True)


class LightRAGEngine:
    _instance = None
    rag: Optional[LightRAG] = None
    _trans_cache: Dict[str, str] = {}
    _dim_meta_file: Path = LIGHTRAG_DIR / "vector_dim.meta"
    _chunks_cache: Dict[str, str] = {}
    _chunks_doc_map: Dict[str, str] = {}  # chunk_id -> file_path
    _chunks_mtime: float = 0

    def __init__(self):
        self.working_dir = str(LIGHTRAG_DIR)
        # 不再在 __init__ 中立即初始化，而是等待 ensure_initialized 被调用

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
                try:
                    if history_messages is None:
                        history_messages = []

                    # [Optimization] Capture retrieval context from LightRAG system prompt
                    if system_prompt and "---Context---" in system_prompt:
                        try:
                            # Create a new context dict for this call
                            current_ctx = {"raw": system_prompt.split("---Context---")[-1]}

                            # 尝试提取具体的实体和 Chunk 列表以供 UI 展示
                            if "---Context---" in system_prompt:
                                context_block = system_prompt.split("---Context---")[-1]
                                current_ctx["raw"] = context_block

                                # Extract Chunks
                                if "Reference Document List" in context_block:
                                    chunks_block = context_block.split("Reference Document List")[-1]
                                    if "####### Knowledge Graph Data" in chunks_block:
                                        chunks_block = chunks_block.split("####### Knowledge Graph Data")[0]
                                    current_ctx["chunks"] = chunks_block.strip()
                                else:
                                    chunks_block = context_block
                                    if "####### Knowledge Graph Data" in chunks_block:
                                        chunks_block = chunks_block.split("####### Knowledge Graph Data")[0]
                                    if "Context:" in chunks_block[:20]:
                                        chunks_block = chunks_block.split("Context:", 1)[-1]
                                    current_ctx["chunks"] = chunks_block.strip()

                                # Extract KG
                                if "Knowledge Graph Data (Entity)" in context_block:
                                    kg_block = context_block.split("Knowledge Graph Data (Entity)")[-1]
                                    if "```json" in kg_block:
                                        kg_part = kg_block.split("```json")[-1].split("```")[0]
                                        current_ctx["entities"] = kg_part.strip()
                            else:
                                if "Reference Document List" in system_prompt:
                                    parts = system_prompt.split("Reference Document List")
                                    if len(parts) > 1:
                                        potential_ctx = parts[-1]
                                        if "---Instructions---" not in potential_ctx:
                                            current_ctx["chunks"] = potential_ctx.split("---")[0].strip()

                            # Set context var
                            last_context_ctx.set(current_ctx)
                        except Exception:
                            pass

                    # Check if context is in prompt instead of system_prompt
                    if not system_prompt and prompt and "---Context---" in prompt:
                        logger.info("[Debug] Context found in user prompt, switching target.")
                        system_prompt = prompt
                        pass
                except Exception:
                    pass

                # [Feature] Dynamic Retrieval Scope Filtering
                try:
                    rv = runtime_vars_ctx.get()
                    filter_doc_id = (rv or {}).get("filter_doc_id")
                    
                    target_prompt = system_prompt
                    is_system = True
                    if not target_prompt and prompt and "---Context---" in prompt:
                        target_prompt = prompt
                        is_system = False

                    if filter_doc_id and target_prompt and "---Context---" in target_prompt:
                        import re

                        marker = f"doc#{filter_doc_id}"
                        parts = target_prompt.split("---Context---")
                        base_prompt = parts[0]
                        context_part = parts[1]

                        kg_header = "####### Knowledge Graph Data (Entity)"
                        kg_split = context_part.split(kg_header)
                        chunks_part = kg_split[0]
                        kg_part = kg_header + kg_split[1] if len(kg_split) > 1 else ""

                        # 1. Filter Chunks in "Reference Document List"
                        if "Reference Document List" in chunks_part:
                            chunk_sections = re.split(r"(\[\d+\])", chunks_part)
                            new_chunks_part = chunk_sections[0]
                            kept_chunks = 0
                            for i in range(1, len(chunk_sections), 2):
                                marker_tag = chunk_sections[i]
                                chunk_body = chunk_sections[i + 1]
                                if marker in chunk_body:
                                    new_chunks_part += marker_tag + chunk_body
                                    kept_chunks += 1
                            chunks_part = new_chunks_part

                        # 2. Filter Entities in "Knowledge Graph Data (Entity)"
                        if kg_part:
                            entities_kept = False
                            try:
                                json_start = kg_part.find("[")
                                json_end = kg_part.rfind("]")
                                if json_start != -1 and json_end != -1:
                                    json_str = kg_part[json_start : json_end + 1]
                                    try:
                                        entities = json.loads(json_str)
                                        if isinstance(entities, list):
                                            filtered_entities = []
                                            for ent in entities:
                                                sid = str(ent.get("source_id", ""))
                                                if marker in sid:
                                                    filtered_entities.append(ent)
                                            
                                            new_kg_json = json.dumps(filtered_entities, ensure_ascii=False, indent=2)
                                            kg_part = (
                                                "####### Knowledge Graph Data (Entity)\n\n```json\n"
                                                + new_kg_json
                                                + "\n```"
                                            )
                                            entities_kept = True
                                    except json.JSONDecodeError:
                                        pass
                            except Exception as e:
                                pass

                            if not entities_kept:
                                kg_part = ""

                        context_part = chunks_part + "\n\n" + kg_part

                        # [Update] Sync _last_context with filtered result
                        try:
                            current_ctx = last_context_ctx.get() or {}
                            if "Reference Document List" in chunks_part:
                                ref_list_part = chunks_part.split("Reference Document List")[-1].split("---")[0]
                                current_ctx["chunks"] = ref_list_part.strip()
                            if kg_part and "```json" in kg_part:
                                kg_json = kg_part.split("```json")[-1].split("```")[0]
                                current_ctx["entities"] = kg_json.strip()
                            last_context_ctx.set(current_ctx)
                        except Exception:
                            pass

                        target_prompt = base_prompt + "---Context---\n" + context_part
                        target_prompt += f"\n\n注意：你当前处于“当前文档”检索模式，必须仅基于 doc#{filter_doc_id} 的内容回答，严禁引用其他文档或你的预训练知识。"
                        
                        if is_system:
                            system_prompt = target_prompt
                        else:
                            prompt = target_prompt
                except Exception as e:
                    logger.error(f"Context filtering failed: {e}")

                # [Feature] Source Reference Appending (Captured for later use)
                captured_context_map = {}
                try:
                    retrieved_context = ""
                    if system_prompt and "---Context---" in system_prompt:
                        retrieved_context = system_prompt.split("---Context---")[-1].strip()
                        if "Reference Document List" in retrieved_context:
                            try:
                                import re
                                ref_section = retrieved_context.split("Reference Document List")[-1]
                                if "####### Knowledge Graph Data" in ref_section:
                                    ref_section = ref_section.split("####### Knowledge Graph Data")[0]
                                chunks = re.split(r"(\[\d+\])", ref_section)
                                for i in range(1, len(chunks), 2):
                                    idx_str = chunks[i].strip("[]")
                                    content = chunks[i + 1].strip()
                                    source_name = "Unknown"
                                    if "Source: " in content:
                                        source_line = content.split("Source: ")[1].split("\n")[0].strip()
                                        source_name = source_line
                                    captured_context_map[idx_str] = {
                                        "source": source_name,
                                        "preview": content[:100].replace("\n", " ") + "...",
                                    }
                            except Exception:
                                pass
                    
                    # Custom Prompt Template Logic
                    qa_prompt_file = getattr(settings, "QA_SYSTEM_PROMPT_FILE", "backend/prompts/qa_system.md")
                    custom_prompt_template = None
                    p = Path(qa_prompt_file)
                    if p.exists():
                        custom_prompt_template = p.read_text(encoding="utf-8").strip()
                    else:
                        custom_prompt_template = getattr(settings, "QA_SYSTEM_PROMPT", None)

                    if custom_prompt_template:
                        from datetime import datetime
                        now = datetime.now().strftime("%Y-%m-%d")
                        rv = runtime_vars_ctx.get() or {}
                        kv = retrieved_context if retrieved_context else rv.get("knowledge", "")
                        hist_str = rv.get("history", "")
                        if not hist_str and history_messages:
                            if isinstance(history_messages, list):
                                lines = []
                                for m in history_messages:
                                    if isinstance(m, dict):
                                        lines.append(f"{m.get('role', 'user')}: {m.get('content', '')}")
                                    else:
                                        lines.append(str(m))
                                hist_str = "\n".join(lines)

                        if kv and len(kv) > 50000:
                            kv = kv[:50000] + "...(truncated)"
                        if hist_str and len(hist_str) > 10000:
                            hist_str = hist_str[-10000:]

                        doc_stats_str = ""
                        try:
                            doc_status_path = LIGHTRAG_DIR / "kv_store_doc_status.json"
                            if doc_status_path.exists():
                                with open(doc_status_path, "r", encoding="utf-8") as f:
                                    status_data = json.load(f)
                                valid_docs = []
                                for k, v in status_data.items():
                                    if v.get("status") == "processed":
                                        fp = v.get("file_path", "Unknown")
                                        if "doc#" in fp and ":" in fp:
                                            fp = fp.split(":", 1)[1]
                                        valid_docs.append(fp)
                                valid_docs.sort()
                                if valid_docs:
                                    doc_stats_str = f"【系统统计信息】\n知识库现有 {len(valid_docs)} 篇已处理文档：\n"
                                    for i, name in enumerate(valid_docs):
                                        doc_stats_str += f"{i + 1}. {name}\n"
                                    doc_stats_str += "\n"
                        except Exception:
                            pass

                        final_knowledge = doc_stats_str + kv
                        system_prompt = (
                            custom_prompt_template.replace("{current_date}", now)
                            .replace("{knowledge}", final_knowledge)
                            .replace("{history}", hist_str)
                        )

                except Exception as e:
                    logger.error(f"Failed to apply custom QA prompt: {e}")
                    pass

                try:
                    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
                    messages = []
                    if "deepseek-reasoner" in model_name and system_prompt:
                        messages.append({"role": "user", "content": f"{system_prompt}\n\n{prompt}"})
                    else:
                        if system_prompt:
                            messages.append({"role": "system", "content": system_prompt})
                        messages.append({"role": "user", "content": prompt})
                    
                    logger.info(f"Calling LLM: {model_name} via base_url={base_url or 'default'}")
                    resp = await client.chat.completions.create(model=model_name, messages=messages, temperature=0)
                    response = resp.choices[0].message.content if (resp and resp.choices) else ""

                except Exception as e:
                    logger.error(f"LLM 调用失败: {e}")
                    response = ""

                if isinstance(response, str):
                    clean_response = response.strip()
                    if "```json" in clean_response:
                        import re
                        match = re.search(r"```json\s*(.*?)\s*```", clean_response, re.DOTALL)
                        if match:
                            clean_response = match.group(1)
                    elif "```" in clean_response:
                        import re
                        match = re.search(r"```\s*(.*?)\s*```", clean_response, re.DOTALL)
                        if match:
                            clean_response = match.group(1)
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
            
            # 自动探测
            try:
                probe_client = (
                    OpenAI(api_key=embed_api_key, base_url=embed_base_url)
                    if embed_base_url
                    else OpenAI(api_key=embed_api_key)
                )
                probe_resp = probe_client.embeddings.create(input=["dim_probe"], model=embed_model_name)
                actual = len(probe_resp.data[0].embedding) if (probe_resp and probe_resp.data) else None
                if actual and actual > 0:
                    embed_dim = actual
            except Exception as _e:
                logger.warning(f"Auto-detect embed dim failed, use heuristic {embed_dim}: {_e}")

            logger.info(f"Initializing LightRAG with model: {embed_model_name}, dim: {embed_dim}")

            async def embedding_func(texts: list[str]) -> np.ndarray:
                from openai import AsyncOpenAI

                client = AsyncOpenAI(api_key=embed_api_key, base_url=embed_base_url)
                resp = await client.embeddings.create(model=embed_model_name, input=texts)
                arr = np.array([d.embedding for d in resp.data], dtype=float)
                # ... normalization logic same as original ...
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
                        out = out[: len(texts), :]
                    return out
                except Exception as e:
                    logger.error(f"Embedding output normalization failed: {e}")
                    return np.zeros((len(texts), embed_dim), dtype=float)

            # Patch openai_embed
            try:
                import lightrag.llm.openai as _lo
                def _patched_openai_embed(texts, model, api_key=None, base_url=None, embedding_dim=None):
                    from openai import OpenAI
                    client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
                    resp = client.embeddings.create(model=model, input=texts)
                    emb = [d.embedding for d in resp.data]
                    return np.array(emb)
                _lo.openai_embed = _patched_openai_embed
            except Exception as e:
                logger.warning(f"Failed to patch openai_embed: {e}")

            # Enhance Prompts
            try:
                import lightrag.prompt as _lp
                if "entity_extraction_system_prompt" in _lp.PROMPTS:
                    _lp.PROMPTS["entity_extraction_system_prompt"] = _lp.PROMPTS[
                        "entity_extraction_system_prompt"
                    ].replace(
                        "Retain proper nouns in their original language",
                        "Translate proper nouns and all entities to Chinese whenever possible to ensure a consistent Chinese Knowledge Graph",
                    )
                    if "Simplified Chinese" not in _lp.PROMPTS["entity_extraction_system_prompt"]:
                        _lp.PROMPTS["entity_extraction_system_prompt"] += """
注意：
1. 请务必使用简体中文输出所有实体名称、类型和描述。
2. 即使原文是英文或其他语言，也请将其翻译为准确、专业的中文术语。
3. 实体描述应详细且完全使用中文。
4. **核心要求：始终将“源文档/文件”提取为一个独立的实体。**
   - 实体类型设为“文件”或“文档”。
   - 尽力从文本标题、页眉或正文中提取其真实名称。
   - 提取文件中的日期信息、作者、来源等作为其实体描述的一部分。
   - **建立联系**：将文中提取的所有其他实体与该“文档”实体建立联系。
5. 保持术语的一致性。
6. **英文规范**：对于必须保留英文的专有名词，请务必使用**标准的大写/混合大小写格式**。
"""
                if "rag_response" in _lp.PROMPTS:
                     _lp.PROMPTS["rag_response"] = """
---Role---
You are a helpful, rigorous, and intelligent assistant. You must answer the user's question based strictly on the provided context (documents and entities).

---Instructions---
1. **Language**: You must answer in **Chinese** (Simplified Chinese).
2. **In-text Citations (MANDATORY)**: 
   - You MUST cite the source for every fact you state.
   - Use the format `[n]` immediately after the sentence or clause, where `n` matches the index in the "Reference Document List".
   - Example: "智能工厂建设加速[1]，产值提升了20%[2]。"
   - DO NOT use `[Source: n]`, `(Source: n)`, or `doc#id`. Only use `[n]`.
3. **No Reference List**: DO NOT generate a list of references at the end. The `[n]` markers in the text are sufficient.
4. **Scope**: Answer ONLY based on the provided context. If the information is not in the context, say "根据已知文档无法回答该问题".

---Context---
{context_data}
"""
            except Exception as e:
                logger.warning(f"Failed to enhance prompts: {e}")

            try:
                self.rag = LightRAG(
                    working_dir=self.working_dir,
                    llm_model_func=llm_model_func,
                    embedding_func=EmbeddingFunc(embedding_dim=embed_dim, max_token_size=8192, func=embedding_func),
                    chunk_token_size=1200,
                    chunk_overlap_token_size=100,
                    addon_params={
                        "language": "Chinese",
                        "entity_types": ["人物", "组织", "地点", "事件", "概念", "方法", "技术", "物品", "其他"],
                    },
                )
            except AssertionError as ae:
                if "Embedding dim mismatch" in str(ae):
                    self._clean_vector_stores()
                    self.rag = LightRAG(
                        working_dir=self.working_dir,
                        llm_model_func=llm_model_func,
                        embedding_func=EmbeddingFunc(embedding_dim=embed_dim, max_token_size=8192, func=embedding_func),
                        chunk_token_size=1200,
                        chunk_overlap_token_size=100,
                        addon_params={
                            "language": "Chinese",
                            "entity_types": ["人物", "组织", "地点", "事件", "概念", "方法", "技术", "物品", "其他"],
                        },
                    )
                else:
                    raise

            # Fix storage dim
            if self.rag:
                for storage_name in ["chunks_vdb", "entities_vdb", "relationships_vdb"]:
                    storage = getattr(self.rag, storage_name, None)
                    if storage and hasattr(storage, "embedding_dim"):
                        if storage.embedding_dim != embed_dim:
                            storage.embedding_dim = embed_dim
                            try:
                                if hasattr(storage, "_client") and hasattr(storage._client, "_data"):
                                    storage._client._data = []
                                    storage._client.dim = embed_dim
                            except Exception:
                                pass

            logger.info("LightRAG 实例创建成功，等待异步初始化存储...")

        except Exception as e:
            logger.error(f"LightRAG 初始化失败: {e}")
            import traceback
            traceback.print_exc()

    async def _ensure_storages_initialized(self):
        if self.rag:
            try:
                if hasattr(self.rag, "initialize_storages"):
                    await self.rag.initialize_storages()
            except Exception as e:
                logger.warning(f"LightRAG 存储初始化警告: {e}")

    def set_runtime_vars(self, knowledge: str = "", history: Optional[List[str]] = None, filter_doc_id: Optional[int] = None):
        runtime_vars_ctx.set(
            {
                "knowledge": knowledge or "",
                "history": "\n".join(history or []) if history else "",
                "filter_doc_id": filter_doc_id,
            }
        )

    def clear_runtime_vars(self):
        runtime_vars_ctx.set(None)

    def get_last_context(self) -> Optional[Dict[str, Any]]:
        return last_context_ctx.get()

    def clear_last_context(self):
        last_context_ctx.set(None)

    def insert_text(self, text: str, description: str = None):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            raise RuntimeError(
                "Cannot call sync insert_text from within a running event loop. Use await insert_text_async instead."
            )
        return asyncio.run(self.insert_text_async(text, description))

    async def insert_text_async(self, text: str, description: str = None):
        logger.info(f"[LightRAG] insert_text_async called. Description: {description}")
        if not self.rag:
            raise RuntimeError("LightRAG not initialized")

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
                return
            except Exception as e:
                last_exception = e
                import asyncio as _asyncio
                await _asyncio.sleep(2 * (i + 1))
        raise last_exception

    def query(self, query: str, mode: str = "mix", top_k: int = 60) -> str:
        if not self.rag:
            self._init_rag()

        if self.rag:
            try:
                try:
                    sig = inspect.signature(QueryParam)
                    kwargs = {"mode": mode, "top_k": top_k}
                    rerank_enabled = getattr(settings, "RERANK_ENABLED", False)
                    if "enable_rerank" in sig.parameters:
                        kwargs["enable_rerank"] = rerank_enabled
                    elif "rerank" in sig.parameters:
                        kwargs["rerank"] = rerank_enabled
                    param = QueryParam(**kwargs)
                except Exception:
                    param = QueryParam(mode=mode)

                result = self.rag.query(query, param=param)
                return result
            except Exception as e:
                logger.error(f"查询失败: {e}")
                return f"查询出错: {str(e)}"
        return "服务未初始化"

    async def call_llm(self, prompt: str, system_prompt: str = None, history_messages: List[Dict] = None) -> str:
        if not self.rag:
            return "服务未初始化"
        try:
            if hasattr(self.rag, "llm_model_func"):
                return await self.rag.llm_model_func(
                    prompt, system_prompt=system_prompt, history_messages=history_messages
                )
            else:
                return "LLM function not available"
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return f"LLM Error: {str(e)}"

    async def query_async(self, query: str, mode: str = "mix", filter_doc_id: Optional[int] = None, top_k: int = 60) -> str:
        if not self.rag:
            return "服务未初始化"
        try:
            if filter_doc_id:
                query = f"Based on doc#{filter_doc_id}: {query}"
                mode = "local"

            try:
                sig = inspect.signature(QueryParam)
                kwargs = {"mode": mode, "top_k": top_k}
                rerank_enabled = getattr(settings, "RERANK_ENABLED", False)
                if "enable_rerank" in sig.parameters:
                    kwargs["enable_rerank"] = rerank_enabled
                elif "rerank" in sig.parameters:
                    kwargs["rerank"] = rerank_enabled
                param = QueryParam(**kwargs)
            except Exception:
                param = QueryParam(mode=mode)
            
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
                    new_cache = {}
                    new_doc_map = {}
                    for k, v in data.items():
                        if isinstance(v, dict):
                            if "content" in v:
                                new_cache[k] = v["content"]
                            if "file_path" in v:
                                new_doc_map[k] = v["file_path"]
                        elif isinstance(v, str):
                            new_cache[k] = v
                    self._chunks_cache = new_cache
                    self._chunks_doc_map = new_doc_map
                    self._chunks_mtime = mtime
            except Exception as e:
                logger.warning(f"Failed to load chunks cache: {e}")

    def search_doc_chunks(self, doc_id: int, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if not self.rag:
            self._init_rag()
        if not self.rag:
            return []

        self._load_chunks_cache()
        marker = f"doc#{doc_id}:"
        candidates = []

        try:
            storage = getattr(self.rag, "chunks_vdb", None)
            if hasattr(storage, "search"):
                fetch_k = max(50, top_k * 10)
                res = storage.search(query, top_k=fetch_k)

                for r in res or []:
                    cid = getattr(r, "id", None) or getattr(r, "__id__", None)
                    if not cid and isinstance(r, dict):
                        cid = r.get("id") or r.get("__id__")

                    if cid and cid in self._chunks_doc_map:
                        fp = self._chunks_doc_map[cid]
                        if marker in fp:
                            preview = ""
                            try:
                                preview = getattr(r, "text", None) or getattr(r, "content", None) or ""
                            except:
                                pass
                            if not preview and cid in self._chunks_cache:
                                preview = self._chunks_cache[cid]

                            score = float(getattr(r, "score", 0.0) or 0.0)
                            candidates.append({"id": cid, "content": preview, "score": score, "file_path": fp})
                    else:
                        preview = ""
                        try:
                            preview = getattr(r, "text", None) or getattr(r, "content", None) or ""
                        except:
                            pass
                        if not preview and cid and cid in self._chunks_cache:
                            preview = self._chunks_cache[cid]

                        if preview and marker in preview:
                            score = float(getattr(r, "score", 0.0) or 0.0)
                            candidates.append(
                                {
                                    "id": cid,
                                    "content": preview,
                                    "score": score,
                                    "file_path": f"doc#{doc_id}:Unknown",
                                }
                            )
                candidates.sort(key=lambda x: x["score"], reverse=True)
                return candidates[:top_k]
        except Exception as e:
            logger.warning(f"LightRAG doc chunk search failed: {e}")
        return []

    def get_graph_data(self, doc: Optional[KnowledgeDocument] = None) -> Dict[str, Any]:
        import networkx as nx
        graphml_path = LIGHTRAG_DIR / "graph_chunk_entity_relation.graphml"
        if not graphml_path.exists():
            return {"nodes": {}, "edges": {}}

        try:
            G = nx.read_graphml(str(graphml_path))
            if doc:
                fname = (doc.filename or "").strip()
                oss_name = Path(doc.oss_key).name if getattr(doc, "oss_key", None) else ""
                marker = f"doc#{doc.id}:" if getattr(doc, "id", None) else ""
                keep = set()
                for node_id, data in G.nodes(data=True):
                    attrs = data or {}
                    fp = str(attrs.get("file_path") or attrs.get("FILE_PATH") or "")
                    sid = str(attrs.get("source_id") or attrs.get("SOURCE_ID") or "")
                    is_match = False
                    if marker:
                        if marker in sid or marker in fp:
                            is_match = True
                    if not is_match and not marker and fname:
                        if fname in fp or (oss_name and oss_name in fp):
                            is_match = True
                    if is_match:
                        keep.add(node_id)
                G = G.subgraph(keep) if keep else nx.Graph()

            nodes = {}
            edges = {}
            pr = {}
            try:
                pr = nx.pagerank(G)
            except Exception:
                pr = {n: d for n, d in G.degree}
            top_nodes_ids = [n for n, _ in sorted(pr.items(), key=lambda x: x[1], reverse=True)[:200]]
            subgraph = G.subgraph(top_nodes_ids)

            for node_id, data in subgraph.nodes(data=True):
                attrs = {k: v for k, v in data.items() if k not in ["entity_type"]}
                nodes[node_id] = {"name": node_id, "type": data.get("entity_type", "Entity"), "attributes": attrs}

            for u, v, data in subgraph.edges(data=True):
                edge_id = f"{u}_{v}"
                edges[edge_id] = {
                    "source": u,
                    "target": v,
                    "label": data.get("description", "related")[:20],
                }

            return {"nodes": nodes, "edges": edges}
        except Exception as e:
            logger.error(f"读取 GraphML 失败: {e}")
            return {"nodes": {}, "edges": {}}

    def _clean_vector_stores(self):
        try:
            removed = 0
            import shutil
            for p in LIGHTRAG_DIR.iterdir():
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
        except Exception:
            pass

    async def rebuild_store(self, db: AsyncSession, exclude_filenames: Optional[List[str]] = None, include_filenames: Optional[List[str]] = None, clear_existing: bool = True):
        await self.ensure_initialized(db)
        try:
            if clear_existing:
                if os.path.exists(self.working_dir):
                    self._clean_vector_stores()
                else:
                    os.makedirs(self.working_dir, exist_ok=True)
            
            self.rag = None
            await self.ensure_initialized(db)
            res = await db.execute(select(KnowledgeDocument).order_by(KnowledgeDocument.created_at.asc()))
            docs = res.scalars().all()
            
            for d in docs:
                if include_filenames and d.filename not in include_filenames:
                    continue
                if exclude_filenames and d.filename and d.filename in exclude_filenames:
                    continue
                
                temp_path = None
                text = ""
                try:
                    if d.oss_key:
                        ext = os.path.splitext(d.filename or "")[1] or ".txt"
                        temp_name = f"temp_rebuild_{d.id}{ext}"
                        temp_path = Path(self.working_dir) / temp_name
                        storage_service.download_file(d.oss_key, str(temp_path))
                        text = parse_local_file(str(temp_path))
                    else:
                        # Assuming UPLOAD_DIR is available in parser or passed down?
                        # Using DATA_DIR/temp as convention
                        candidate = DATA_DIR / "temp" / (d.filename or "")
                        if candidate.exists():
                            text = parse_local_file(str(candidate))
                    
                    if text:
                        await self.insert_text_async(text, description=f"doc#{d.id}:{d.filename}")
                finally:
                    if temp_path and os.path.exists(temp_path):
                        try:
                            os.remove(temp_path)
                        except Exception:
                            pass
        except Exception as e:
            logger.error(f"LightRAG rebuild failed: {e}")

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
                        preview = getattr(r, "text", None) or getattr(r, "content", None) or ""
                        score = float(getattr(r, "score", 0.0) or 0.0)
                    except Exception:
                        pass
                    items.append(
                        {"title": "", "url": None, "page": None, "score": score, "preview": (preview or "")[:200]}
                    )
                return items
        except Exception as e:
            logger.warning(f"LightRAG chunk search failed: {e}")
        return []

    def search_entities(self, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
        if not self.rag:
            self._init_rag()
        if not self.rag:
            return []
        try:
            storage = getattr(self.rag, "entities_vdb", None)
            if hasattr(storage, "search"):
                res = storage.search(query, top_k=top_k)
                items = []
                for r in res or []:
                    entity_name = ""
                    score = 0.0
                    try:
                        entity_name = (
                            getattr(r, "entity_name", None)
                            or getattr(r, "id", None)
                            or getattr(r, "__id__", None)
                            or ""
                        )
                        score = float(getattr(r, "score", 0.0) or 0.0)
                    except Exception:
                        pass

                    if entity_name:
                        items.append({"entity_name": entity_name, "score": score})
                return items
        except Exception as e:
            logger.warning(f"LightRAG entity search failed: {e}")
        return []


lightrag_engine = LightRAGEngine.get_instance()
