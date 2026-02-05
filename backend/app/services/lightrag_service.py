import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import asyncio
import numpy as np
import time
import contextvars

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
import inspect

logger = logging.getLogger(__name__)

# ContextVars for request-scoped state
runtime_vars_ctx = contextvars.ContextVar("runtime_vars", default=None)
last_context_ctx = contextvars.ContextVar("last_context", default=None)

# 数据存储目录
# Fix: Use absolute path relative to backend directory to avoid CWD dependency
BACKEND_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BACKEND_DIR / "data"
LIGHTRAG_DIR = DATA_DIR / "lightrag_store"
LIGHTRAG_DIR.mkdir(parents=True, exist_ok=True)

class LightRAGService:
    _instance = None
    rag: Optional[LightRAG] = None
    _trans_cache: Dict[str, str] = {}
    _dim_meta_file: Path = LIGHTRAG_DIR / "vector_dim.meta"
    _chunks_cache: Dict[str, str] = {}
    _chunks_doc_map: Dict[str, str] = {} # chunk_id -> file_path
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
                                    # Split by KG header if present, or take all
                                    chunks_block = context_block.split("Reference Document List")[-1]
                                    if "####### Knowledge Graph Data" in chunks_block:
                                        chunks_block = chunks_block.split("####### Knowledge Graph Data")[0]
                                    current_ctx["chunks"] = chunks_block.strip()
                                else:
                                    # Fallback: Assume everything before KG data is chunks
                                    chunks_block = context_block
                                    if "####### Knowledge Graph Data" in chunks_block:
                                        chunks_block = chunks_block.split("####### Knowledge Graph Data")[0]
                                    # Also check for "Context:" header just in case
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
                                # Fallback for legacy prompts or unexpected formats
                                if "Reference Document List" in system_prompt:
                                    # Be careful not to match the prompt instruction itself
                                    parts = system_prompt.split("Reference Document List")
                                    # The last part is likely the context if it exists
                                    if len(parts) > 1:
                                        potential_ctx = parts[-1]
                                        # Heuristic: context usually doesn't contain "---Instructions---"
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
                # If filter_doc_id is set, we strip out any context not belonging to that doc.
                try:
                    rv = runtime_vars_ctx.get()
                    filter_doc_id = (rv or {}).get("filter_doc_id")
                    logger.info(f"[Debug] filter_doc_id: {filter_doc_id}, system_prompt_len: {len(system_prompt) if system_prompt else 0}")
                    if prompt:
                         logger.info(f"[Debug] prompt_preview: {prompt[:200]}")
                    
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
                        
                        # Split context into chunks part and KG part to safely filter both
                        kg_header = "####### Knowledge Graph Data (Entity)"
                        kg_split = context_part.split(kg_header)
                        chunks_part = kg_split[0]
                        kg_part = kg_header + kg_split[1] if len(kg_split) > 1 else ""
                        
                        # 1. Filter Chunks in "Reference Document List"
                        if "Reference Document List" in chunks_part:
                            chunk_sections = re.split(r"(\[\d+\])", chunks_part)
                            new_chunks_part = chunk_sections[0]
                            kept_chunks = 0
                            total_chunks = 0
                            for i in range(1, len(chunk_sections), 2):
                                marker_tag = chunk_sections[i]
                                chunk_body = chunk_sections[i+1]
                                total_chunks += 1
                                # Check if this chunk belongs to our doc
                                if marker in chunk_body:
                                    new_chunks_part += marker_tag + chunk_body
                                    kept_chunks += 1
                                else:
                                    # Log skipped chunk title for debug
                                    title_preview = chunk_body.strip().split('\n')[0][:50]
                                    logger.debug(f"[Debug] Skipped chunk: {title_preview}")
                            
                            chunks_part = new_chunks_part
                            logger.info(f"[Debug] Filtered chunks: kept {kept_chunks}/{total_chunks} for marker {marker}")

                        # 2. Filter Entities in "Knowledge Graph Data (Entity)"
                        if kg_part:
                            entities_kept = False
                            try:
                                # [Robustness] Try to find JSON list within the block
                                json_start = kg_part.find("[")
                                json_end = kg_part.rfind("]")
                                if json_start != -1 and json_end != -1:
                                    json_str = kg_part[json_start:json_end+1]
                                    try:
                                        entities = json.loads(json_str)
                                        if isinstance(entities, list):
                                            filtered_entities = []
                                            for ent in entities:
                                                # Check source_id. LightRAG might store it as string or list?
                                                # Usually "doc_id" or "source_id"
                                                sid = str(ent.get("source_id", ""))
                                                if marker in sid:
                                                    filtered_entities.append(ent)
                                            
                                            # Reconstruct KG part
                                            new_kg_json = json.dumps(filtered_entities, ensure_ascii=False, indent=2)
                                            kg_part = "####### Knowledge Graph Data (Entity)\n\n```json\n" + new_kg_json + "\n```"
                                            entities_kept = True
                                            logger.info(f"[Debug] Filtered entities: kept {len(filtered_entities)}/{len(entities)} for {marker}")
                                    except json.JSONDecodeError:
                                        logger.warning("[Debug] Failed to decode entities JSON")
                            except Exception as e:
                                logger.warning(f"Failed to filter entities in context: {e}")
                                
                            # [Strict] If parsing failed or no entities match, drop the whole KG part to prevent leakage
                            if not entities_kept:
                                logger.info("[Debug] Dropping all entities (strict mode or parsing failed).")
                                kg_part = ""
                                
                        context_part = chunks_part + "\n\n" + kg_part
                        
                        # [Update] Sync _last_context with filtered result so UI sources are accurate
                        try:
                            # Update existing context var
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
                        # [Refinement] Add a strict document scope reminder
                        target_prompt += f"\n\n注意：你当前处于“当前文档”检索模式，必须仅基于 doc#{filter_doc_id} 的内容回答，严禁引用其他文档或你的预训练知识。"
                        logger.info(f"Filtered context to doc#{filter_doc_id}")
                        
                        if is_system:
                            system_prompt = target_prompt
                        else:
                            prompt = target_prompt
                except Exception as e:
                    logger.error(f"Context filtering failed: {e}")

                # [Feature] Source Reference Appending
                # We need to capture the context to map [n] to sources later
                captured_context_map = {} # {index: {source, content}}
                
                try:
                    from app.core.config import settings as _s
                    
                    # 1. Extract context from the current system_prompt
                    retrieved_context = ""
                    if system_prompt and "---Context---" in system_prompt:
                        retrieved_context = system_prompt.split("---Context---")[-1].strip()
                        
                        # Parse Reference Document List for Source Mapping
                        if "Reference Document List" in retrieved_context:
                            try:
                                import re
                                # Extract blocks like [1] ... [2] ...
                                ref_section = retrieved_context.split("Reference Document List")[-1]
                                if "####### Knowledge Graph Data" in ref_section:
                                    ref_section = ref_section.split("####### Knowledge Graph Data")[0]
                                
                                # Regex to find [n] and content until next [n+1]
                                chunks = re.split(r"(\[\d+\])", ref_section)
                                for i in range(1, len(chunks), 2):
                                    idx_str = chunks[i].strip("[]") # "1"
                                    content = chunks[i+1].strip()
                                    
                                    # Extract Source: filename from content
                                    # Typical content: "Source: filename\nContent..."
                                    source_name = "Unknown"
                                    if "Source: " in content:
                                        # Extract until newline
                                        source_line = content.split("Source: ")[1].split("\n")[0].strip()
                                        source_name = source_line
                                    
                                    captured_context_map[idx_str] = {
                                        "source": source_name,
                                        "preview": content[:100].replace("\n", " ") + "..."
                                    }
                            except Exception as e:
                                logger.warning(f"Failed to parse context for sources: {e}")

                    # 2. Load the custom system prompt template
                    qa_prompt_file = getattr(_s, "QA_SYSTEM_PROMPT_FILE", "backend/prompts/qa_system.md")
                    custom_prompt_template = None
                    p = Path(qa_prompt_file)
                    if p.exists():
                        custom_prompt_template = p.read_text(encoding="utf-8").strip()
                    else:
                        custom_prompt_template = getattr(_s, "QA_SYSTEM_PROMPT", None)
                    
                    # 3. If we have a custom template, we use it to construct the final system prompt
                    if custom_prompt_template:
                        from datetime import datetime
                        now = datetime.now().strftime("%Y-%m-%d")
                        
                        rv = runtime_vars_ctx.get() or {}
                        
                        # Knowledge: Prioritize retrieved context, fallback to runtime var
                        kv = retrieved_context if retrieved_context else rv.get("knowledge", "")
                        
                        # History: Prioritize runtime var (usually set by API), fallback to history_messages
                        hist_str = rv.get("history", "")
                        if not hist_str and history_messages:
                            # Simple formatting
                            if isinstance(history_messages, list):
                                lines = []
                                for m in history_messages:
                                    if isinstance(m, dict):
                                        lines.append(f"{m.get('role', 'user')}: {m.get('content', '')}")
                                    else:
                                        lines.append(str(m))
                                hist_str = "\n".join(lines)
                        
                        # Apply limits (Increased from 6000/2000 to 50000/10000)
                        # 3 documents can easily exceed 6000 chars.
                        if kv and len(kv) > 50000:
                            kv = kv[:50000] + "...(truncated)"
                        if hist_str and len(hist_str) > 10000:
                            hist_str = hist_str[-10000:] # Keep recent history
                            
                        # [Feature] Inject Document Statistics (Count & Names) from Metadata
                        # User Request: Use existing kv_store_doc_status.json instead of counting chunks
                        doc_stats_str = ""
                        try:
                            doc_status_path = LIGHTRAG_DIR / "kv_store_doc_status.json"
                            if doc_status_path.exists():
                                try:
                                    with open(doc_status_path, "r", encoding="utf-8") as f:
                                        status_data = json.load(f)
                                    
                                    # Extract valid docs (status='processed')
                                    valid_docs = []
                                    for k, v in status_data.items():
                                        if v.get("status") == "processed":
                                            fp = v.get("file_path", "Unknown")
                                            # Cleanup: doc#1:filename.txt -> filename.txt
                                            if "doc#" in fp and ":" in fp:
                                                fp = fp.split(":", 1)[1]
                                            valid_docs.append(fp)
                                    
                                    # Sort for consistency
                                    valid_docs.sort()
                                    
                                    if valid_docs:
                                        doc_stats_str = f"【系统统计信息】\n知识库现有 {len(valid_docs)} 篇已处理文档：\n"
                                        for i, name in enumerate(valid_docs):
                                            doc_stats_str += f"{i+1}. {name}\n"
                                        doc_stats_str += "\n"
                                        
                                except Exception as e:
                                    logger.warning(f"Failed to read doc status json: {e}")
                        except Exception as e:
                            logger.warning(f"Failed to generate doc stats from metadata: {e}")

                        # Replace placeholders
                        # Prepend doc_stats to knowledge
                        final_knowledge = doc_stats_str + kv
                        
                        system_prompt = custom_prompt_template.replace("{current_date}", now) \
                                                              .replace("{knowledge}", final_knowledge) \
                                                              .replace("{history}", hist_str)
                        
                        logger.info(f"Applied custom QA prompt from {qa_prompt_file}. Knowledge len: {len(final_knowledge)}, History len: {len(hist_str)}")
                    
                    # If no custom template, we keep the original system_prompt (which has context)
                    
                except Exception as e:
                    logger.error(f"Failed to apply custom QA prompt: {e}")
                    # Fallback: keep original system_prompt
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

                    # [Feature] Post-process response to append sources
                    # [Fix] Disabled in llm_model_func to prevent double source appending in QA stream
                    # The QA service handles source extraction and display explicitly.
                    # if response and captured_context_map:
                    #     try:
                    #         import re
                    #         # Find all citations like [1], [2]
                    #         citations = re.findall(r"\[(\d+)\]", response)
                    #         unique_idxs = sorted(list(set(citations)), key=lambda x: int(x))
                    #         
                    #         if unique_idxs:
                    #             append_lines = ["\n\n**知识来源：**"]
                    #             used_sources = set()
                    #             
                    #             # Check mode: Local (filter_doc_id set) or Global
                    #             rv = runtime_vars_ctx.get()
                    #             is_local_mode = (rv or {}).get("filter_doc_id") is not None
                    #             
                    #             for idx in unique_idxs:
                    #                 if idx in captured_context_map:
                    #                     info = captured_context_map[idx]
                    #                     if is_local_mode:
                    #                         # Local mode: Show chunk preview
                    #                         append_lines.append(f"- [{idx}] {info['preview']}")
                    #                     else:
                    #                         # Global mode: Show document filename (deduplicated)
                    #                         src = info['source']
                    #                         # Clean up doc#id prefix if present for display
                    #                         if "doc#" in src:
                    #                              # Try to extract filename part: doc#1:filename.txt -> filename.txt
                    #                              if ":" in src:
                    #                                  src = src.split(":", 1)[1]
                    #                         
                    #                         append_lines.append(f"- [{idx}] {src}")
                    #             
                    #             response += "\n" + "\n".join(append_lines)
                    #     except Exception as e:
                    #         logger.warning(f"Failed to append sources: {e}")

                except Exception as e:
                    logger.error(f"LLM 调用失败: {e}")
                    response = ""

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
                
                if "entity_extraction_system_prompt" in _lp.PROMPTS:
                    _lp.PROMPTS["entity_extraction_system_prompt"] = _lp.PROMPTS["entity_extraction_system_prompt"].replace(
                        "Retain proper nouns in their original language",
                        "Translate proper nouns and all entities to Chinese whenever possible to ensure a consistent Chinese Knowledge Graph"
                    )
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
6. **英文规范**：对于必须保留英文的专有名词（如 OpenAI, AI, Transformer），请务必使用**标准的大写/混合大小写格式**，严禁使用全小写（如禁止使用 openai, ai），以确保跨文档的实体能正确关联。
"""

                if "rag_response" in _lp.PROMPTS:
                    # Reset to base and apply our custom strict prompt
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
                    logger.info("Replaced LightRAG rag_response prompt with strict Chinese citation version")
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

    def set_runtime_vars(self, knowledge: str = "", history: Optional[List[str]] = None, filter_doc_id: Optional[int] = None):
        runtime_vars_ctx.set({
            "knowledge": knowledge or "",
            "history": "\n".join(history or []) if history else "",
            "filter_doc_id": filter_doc_id
        })

    def clear_runtime_vars(self):
        runtime_vars_ctx.set(None)

    def get_last_context(self) -> Optional[Dict[str, Any]]:
        return last_context_ctx.get()

    def clear_last_context(self):
        last_context_ctx.set(None)

    def insert_text(self, text: str, description: str = None):
        """
        [Sync Wrapper] 向知识库插入文本。
        注意：此方法仅应在同步环境（如脚本、CLI）中使用。
        如果在异步环境（如 FastAPI 路由）中，请务必使用 insert_text_async。
        """
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
            
        if loop and loop.is_running():
            logger.error("Attempted to call sync insert_text from a running event loop.")
            raise RuntimeError("Cannot call sync insert_text from within a running event loop. Use await insert_text_async instead.")
            
        return asyncio.run(self.insert_text_async(text, description))

    async def insert_text_async(self, text: str, description: str = None):
        logger.info(f"[LightRAG] insert_text_async called. Description: {description}, Text length: {len(text)}")
        if not self.rag:
            raise RuntimeError("LightRAG not initialized")
        
        # Log expected chunks (approximate)
        chunk_size = self.rag.chunk_token_size
        est_chunks = len(text) // (chunk_size * 2) 
        logger.info(f"[LightRAG] Async Estimated chunks: ~{est_chunks if est_chunks > 0 else 1}")

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
                except Exception as e:
                    logger.warning(f"LightRAG _insert_done failed in async insert: {e}")
                logger.info(f"文本异步插入成功 (Desc: {description})")
                return
            except Exception as e:
                last_exception = e
                try:
                    msg = str(e)
                    if "history_messages" in msg:
                        pass
                    else:
                        logger.warning(f"异步文本插入失败 (尝试 {i+1}/{retries}): {e}")
                except Exception:
                    logger.warning(f"异步文本插入失败 (尝试 {i+1}/{retries}): {e}")
                import asyncio as _asyncio
                await _asyncio.sleep(2 * (i + 1))
        logger.error(f"文本异步插入最终失败 (Desc: {description})，重试 {retries} 次: {last_exception}")
        raise last_exception

    def query(self, query: str, mode: str = "mix", top_k: int = 60) -> str:
        """
        执行查询。
        :param mode: "naive", "local", "global", "hybrid", "mix"
        :param top_k: Number of chunks/entities to retrieve (default 60, typical limit to avoid context overflow)
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
                
                try:
                    sig = inspect.signature(QueryParam)
                    kwargs = {"mode": mode}
                    
                    # [Feature] Configurable Top-K and Reranking
                    kwargs["top_k"] = top_k
                    
                    rerank_enabled = getattr(settings, "RERANK_ENABLED", False)
                    if "enable_rerank" in sig.parameters:
                        kwargs["enable_rerank"] = rerank_enabled
                    elif "rerank" in sig.parameters:
                        kwargs["rerank"] = rerank_enabled
                    param = QueryParam(**kwargs)
                except Exception:
                    # Fallback if QueryParam signature changes
                    param = QueryParam(mode=mode)
                
                logger.info(f"LightRAG query: {query} (mode={mode}, top_k={top_k}, rerank={getattr(settings, 'RERANK_ENABLED', False)})")
                
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

    async def call_llm(self, prompt: str, system_prompt: str = None, history_messages: List[Dict] = None) -> str:
        """
        Directly call the configured LLM function.
        Useful for manual QA pipelines where context is pre-constructed.
        """
        if not self.rag:
            return "服务未初始化"
        try:
            # Reuse the internal LLM function which handles API calls, logging, and some post-processing
            if hasattr(self.rag, "llm_model_func"):
                return await self.rag.llm_model_func(prompt, system_prompt=system_prompt, history_messages=history_messages)
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
                # If we have a doc filter, we should try to bias the query 
                # to help LightRAG's internal retrieval find relevant chunks.
                query = f"Based on doc#{filter_doc_id}: {query}"
                # Use "local" mode for single document focus to avoid global hallucination/noise
                mode = "local"
            
            try:
                sig = inspect.signature(QueryParam)
                kwargs = {"mode": mode}
                
                # [Feature] Configurable Top-K and Reranking
                kwargs["top_k"] = top_k
                
                rerank_enabled = getattr(settings, "RERANK_ENABLED", False)
                if "enable_rerank" in sig.parameters:
                    kwargs["enable_rerank"] = rerank_enabled
                elif "rerank" in sig.parameters:
                    kwargs["rerank"] = rerank_enabled
                param = QueryParam(**kwargs)
            except Exception:
                param = QueryParam(mode=mode)
            logger.info(f"LightRAG aquery: {query} (mode={mode}, filter_doc={filter_doc_id}, top_k={top_k}, rerank={getattr(settings, 'RERANK_ENABLED', False)})")
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
        """
        Search chunks restricted to a specific document ID.
        Uses manual filtering after vector search.
        """
        if not self.rag:
            self._init_rag()
        if not self.rag:
            return []
            
        # Ensure cache is loaded
        self._load_chunks_cache()
        
        # Use colon to prevent partial matching (e.g. doc#1 matching doc#10)
        marker = f"doc#{doc_id}:"
        candidates = []
        
        try:
            storage = getattr(self.rag, "chunks_vdb", None)
            if hasattr(storage, "search"):
                # Retrieve more candidates to allow for filtering
                # Rule of thumb: top_k * 10 or at least 50
                fetch_k = max(50, top_k * 10)
                res = storage.search(query, top_k=fetch_k)
                
                for r in res or []:
                    # Get ID
                    cid = getattr(r, "id", None) or getattr(r, "__id__", None)
                    if not cid:
                        # Try to find ID from result dict if it's a dict
                        if isinstance(r, dict):
                            cid = r.get("id") or r.get("__id__")
                    
                    # If ID found, check metadata map
                    if cid and cid in self._chunks_doc_map:
                        fp = self._chunks_doc_map[cid]
                        # Check if file_path contains doc#{doc_id}
                        if marker in fp:
                            # Valid chunk
                            preview = ""
                            try:
                                preview = (getattr(r, "text", None) or getattr(r, "content", None) or "")
                            except: pass
                            
                            # Fallback to cache if preview empty
                            if not preview and cid in self._chunks_cache:
                                preview = self._chunks_cache[cid]
                                
                            score = float(getattr(r, "score", 0.0) or 0.0)
                            candidates.append({
                                "id": cid,
                                "content": preview,
                                "score": score,
                                "file_path": fp
                            })
                    else:
                        # [Fix] Fallback: Check if content contains the marker
                        # Since we prepend metadata to content, this is a reliable fallback
                        preview = ""
                        try:
                            preview = (getattr(r, "text", None) or getattr(r, "content", None) or "")
                        except: pass
                        
                        if not preview and cid and cid in self._chunks_cache:
                            preview = self._chunks_cache[cid]
                        
                        if preview and marker in preview:
                             score = float(getattr(r, "score", 0.0) or 0.0)
                             candidates.append({
                                "id": cid,
                                "content": preview,
                                "score": score,
                                "file_path": f"doc#{doc_id}:Unknown" # Construct a dummy path
                            })
                            
                # Sort by score
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
                # [Fix] Add colon to ensure exact prefix match (e.g. doc#1: vs doc#10:)
                marker = f"doc#{doc.id}:" if getattr(doc, "id", None) else ""
                keep = set()
                for node_id, data in G.nodes(data=True):
                    attrs = data or {}
                    fp = str(attrs.get("file_path") or attrs.get("FILE_PATH") or "")
                    sid = str(attrs.get("source_id") or attrs.get("SOURCE_ID") or "")
                    
                    # [Fix] Strict filtering by doc marker (doc#ID)
                    # We avoid loose filename matching which causes cross-document pollution
                    is_match = False
                    if marker:
                         if marker in sid or marker in fp:
                             is_match = True
                    
                    # Fallback only if marker is missing (should not happen for valid docs)
                    # And only if strict matching wasn't attempted
                    if not is_match and not marker and fname:
                        if fname in fp or (oss_name and oss_name in fp):
                            is_match = True
                            
                    if is_match:
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
            logger.info(f"[LightRAG] Graph loaded. Nodes: {len(nodes)}, Edges: {len(edges)}")
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

    def search_entities(self, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
        """
        Perform semantic search on entities vector database.
        """
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
                        # LightRAG entity vdb usually stores entity_name in "entity_name" or "id"
                        entity_name = (getattr(r, "entity_name", None) or getattr(r, "id", None) or getattr(r, "__id__", None) or "")
                        score = float(getattr(r, "score", 0.0) or 0.0)
                    except Exception:
                        pass
                    
                    if entity_name:
                        items.append({"entity_name": entity_name, "score": score})
                return items
        except Exception as e:
            logger.warning(f"LightRAG entity search failed: {e}")
        return []

    async def rebuild_store(self, db: AsyncSession, exclude_filenames: Optional[List[str]] = None, include_filenames: Optional[List[str]] = None, clear_existing: bool = True):
        await self.ensure_initialized(db)
        try:
            import shutil
            if clear_existing:
                if os.path.exists(self.working_dir):
                    logger.info(f"Clearing working directory: {self.working_dir}")
                    # Use the backup method
                    self._backup_and_clear_dir(Path(self.working_dir))
                else:
                    os.makedirs(self.working_dir, exist_ok=True)
            
            self.rag = None
            await self.ensure_initialized(db)
            res = await db.execute(select(KnowledgeDocument).order_by(KnowledgeDocument.created_at.asc()))
            docs = res.scalars().all()
            logger.info(f"Found {len(docs)} documents to rebuild.")
            
            for i, d in enumerate(docs):
                logger.info(f"Processing document {i+1}/{len(docs)}: {d.filename} (ID: {d.id})")
                if include_filenames and d.filename not in include_filenames:
                    continue
                if exclude_filenames and d.filename and d.filename in exclude_filenames:
                    logger.info(f"Skipping excluded file: {d.filename}")
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
                        # self.insert_text(text, description=f"doc#{d.id}:{d.filename}")
                        await self.insert_text_async(text, description=f"doc#{d.id}:{d.filename}")
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
