import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.knowledge import KnowledgeDocument
from app.models.llm_model import LLMModel
from app.services.rag.parser import parse_local_file
from app.services.llm.factory import ModelFactory
from app.services.storage.service import storage_service

logger = logging.getLogger(__name__)

# 路径配置
# app/services/rag/knowledge_base.py -> backend/app/services/rag -> parents[3] = backend
BACKEND_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BACKEND_DIR / "data"
LANCEDB_DIR = DATA_DIR / "lancedb"
# Use "temp" for temporary processing files to distinguish from persistent storage
UPLOAD_DIR = DATA_DIR / "temp"

# 确保必要的目录存在
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
LANCEDB_DIR.mkdir(parents=True, exist_ok=True)


class KnowledgeBaseService:
    """
    知识库服务类，负责管理向量数据库、文档索引和知识图谱提取。
    实现了单例模式。
    """

    _instance = None

    def __init__(self):
        # 默认配置（从环境变量加载）
        self._init_default()

    def _init_default(self):
        """
        初始化默认配置（LightRAG 路径已接管，保持占位即可）。
        """
        self.embedder_config = {}
        self.vector_db = None
        self.knowledge = None

    @classmethod
    def get_instance(cls):
        """
        获取单例实例。
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def reload_config(self, db: AsyncSession):
        """
        兼容接口：确保 LightRAG 根据数据库中当前模型配置完成初始化。
        """
        try:
            from app.services.rag.engines.lightrag import lightrag_engine

            await lightrag_engine.ensure_initialized(db)
            logger.info("LightRAG 已根据数据库配置完成初始化")
        except Exception as e:
            logger.error(f"重新加载知识库配置失败: {e}")

    def index_document(self, file_path: str):
        logger.info(f"Starting LightRAG index_document for file: {file_path}")
        try:
            text = parse_local_file(file_path)
            if not text:
                raise RuntimeError("解析到的文本为空")
            from app.services.rag.engines.lightrag import lightrag_engine

            lightrag_engine.insert_text(text, description=Path(file_path).name)
            return True
        except Exception as e:
            logger.error(f"索引文档失败 {file_path}: {e}")
            raise e

    def search(self, query: str, allowed_names: Optional[List[str]] = None, min_score: float = 0.0, top_k: int = 5):
        refs: List[Dict[str, Any]] = []
        filtered: List[Dict[str, Any]] = []
        try:
            from app.services.rag.engines.lightrag import lightrag_engine

            items = lightrag_engine.search_chunks(query, top_k=top_k)
            for it in items:
                name = it.get("title") or ""
                score = float(it.get("score") or 0.0)
                if allowed_names and name and name not in allowed_names:
                    filtered.append({"title": name, "score": score})
                    continue
                if score is not None and score < (min_score or 0.0):
                    filtered.append({"title": name, "score": score})
                    continue
                refs.append(
                    {
                        "title": name,
                        "url": it.get("url"),
                        "page": it.get("page"),
                        "score": score,
                        "preview": it.get("preview") or "",
                    }
                )
        except Exception as e:
            logger.warning(f"搜索错误: {e}")
        return refs, filtered

    def _chunk_text(self, text: str, chunk_size: int = None, overlap: int = None) -> List[str]:

        strategy = (settings.CHUNK_STRATEGY or "semantic").lower()
        size = chunk_size or settings.CHUNK_SIZE or 1200
        ov = overlap or settings.CHUNK_OVERLAP or 120
        if strategy == "fixed":
            chunks = []
            start = 0
            L = len(text)
            while start < L:
                end = min(start + size, L)
                chunks.append(text[start:end])
                start = end - ov
                if start >= end:
                    start = end
            return chunks
        paras = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not paras:
            paras = [text]
        import re

        def split_sentences(t: str) -> List[str]:
            t = t.replace("\r", "\n")
            sents = re.split(r"(?<=[。！？!?；;．.])\s+", t)
            sents = [s.strip() for s in sents if s.strip()]
            return sents

        token_count = None
        if settings.CHUNK_TOKENIZER:
            try:
                import tiktoken

                enc = tiktoken.get_encoding(settings.CHUNK_TOKENIZER)
                token_count = lambda s: len(enc.encode(s))
            except Exception:
                token_count = None

        def measure(s: str) -> int:
            if token_count:
                return token_count(s)
            return len(s)

        chunks = []
        cur = []
        cur_len = 0
        sentences = []
        for p in paras:
            sentences.extend(split_sentences(p))
        for sent in sentences:
            m = measure(sent)
            if cur_len + m <= size or not cur:
                cur.append(sent)
                cur_len += m
            else:
                chunks.append("".join(cur))
                overlap_sents = []
                if ov > 0:
                    rev = []
                    acc = 0
                    for s in reversed(cur):
                        ms = measure(s)
                        if acc + ms <= ov:
                            rev.append(s)
                            acc += ms
                        else:
                            break
                    overlap_sents = list(reversed(rev))
                cur = overlap_sents + [sent]
                cur_len = sum(measure(s) for s in cur)
        if cur:
            chunks.append("".join(cur))
        return chunks

    def _embed_texts(self, texts: List[str]) -> List[List[float]]:
        try:
            cfg = self.embedder_config or {}
            api_key = cfg.get("api_key")
            base_url = cfg.get("base_url")
            model_id = cfg.get("id") or "text-embedding-3-small"
            from openai import OpenAI

            client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
            resp = client.embeddings.create(model=model_id, input=texts)
            return [d.embedding for d in resp.data]
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            return []

    def delete_document(self, filename: str):
        try:
            from app.db.session import AsyncSessionLocal
            from app.services.rag.engines.lightrag import lightrag_engine

            async def _run():
                async with AsyncSessionLocal() as db:
                    await lightrag_engine.rebuild_store(db, exclude_filenames=[filename])

            import asyncio

            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            if loop.is_running():
                fut = asyncio.run_coroutine_threadsafe(_run(), loop)
                fut.result()
            else:
                loop.run_until_complete(_run())
        except Exception as e:
            logger.error(f"删除文档失败 {filename}: {e}")
        return {"status": "deleted"}

    async def _extract_subgraph(self, text: str, model_config: LLMModel) -> Dict[str, Any]:
        """
        辅助函数：调用 LLM 从文本块中提取子图谱。
        :param text: 文本切片
        :param model_config: LLM 模型配置
        :return: 包含 nodes 和 edges 的字典
        """
        llm = ModelFactory.create_model(model_config)
        logger.info(f"Start extracting subgraph via LLM (fallback). Text len: {len(text)}")

        # 提示词工程：要求 LLM 提取实体、关系及详细属性
        prompt = f"""
You are a knowledge graph extractor. Extract key entities (nodes) and relationships (edges) from the following text.
Return ONLY a valid JSON object (no markdown, no thinking) with the following structure:
{{
  "nodes": {{
    "node_id_1": {{
        "name": "Entity Name", 
        "type": "Person/Location/Concept", 
        "attributes": {{
            "role": "CEO", 
            "date": "2023-01-01", 
            "description": "..."
        }}
    }},
    ...
  }},
  "edges": {{
    "edge_id_1": {{"source": "node_id_1", "target": "node_id_2", "label": "relationship_type"}},
    ...
  }}
}}
Limit to top 30 most important entities and relationships. Ensure source/target IDs exist in nodes.
Do NOT use "Concept A", "Concept B" or similar generic names. Extract REAL entities from the text.
Extract rich attributes for each entity where possible (e.g. timestamps, roles, values, status).

Text:
{text}
        """
        try:
            # 暂时禁用 Agno 日志以避免错误
            import logging

            from agno.models.message import Message

            logging.getLogger("agno").setLevel(logging.WARNING)

            # 显式构造 Message 对象列表，避免字符串处理错误
            messages = [Message(role="user", content=prompt)]
            response = llm.response(messages=messages)

            content = ""
            # 兼容处理不同类型的 LLM 响应（对象、字符串、流式迭代器）
            if hasattr(response, "content"):
                content = response.content or ""
            elif isinstance(response, str):
                content = response
            elif hasattr(response, "__iter__"):
                try:
                    chunks = []
                    for chunk in response:
                        if hasattr(chunk, "content"):
                            chunks.append(str(chunk.content or ""))
                        elif isinstance(chunk, str):
                            chunks.append(chunk)
                        else:
                            chunks.append(str(chunk))
                    content = "".join(chunks)
                except Exception:
                    content = str(response)
            else:
                try:
                    content = str(response)
                except:
                    content = ""

            logger.debug(f"LLM Chunk Response (First 200 chars): {content[:200]}...")

            # 清洗思考过程内容 (针对 DeepSeek R1 等模型)
            if "<think>" in content and "</think>" in content:
                content = content.split("</think>")[-1].strip()

            # 清洗 Markdown 格式
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            content = content.strip()

            try:
                graph_data = json.loads(content)
                nodes_count = len(graph_data.get("nodes", {}))
                edges_count = len(graph_data.get("edges", {}))
                logger.info(f"Subgraph extraction success. Nodes: {nodes_count}, Edges: {edges_count}")
                return graph_data
            except json.JSONDecodeError as je:
                logger.error(f"Chunk JSON 解析错误: {je}")
                return {}

        except Exception as e:
            logger.error(f"子图提取错误: {e}")
            import traceback

            traceback.print_exc()
            return {}

    async def get_document_graph_local(
        self, db: AsyncSession, doc_id: int, force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        获取指定文档的知识图谱子图（基于 LightRAG GraphML）。
        通过节点属性中的来源标识（file_path/source_id）按 doc_id 过滤后，再进行归一化选取。
        """
        try:
            from app.services.rag.engines.lightrag import lightrag_engine

            await lightrag_engine.ensure_initialized(db)
            doc = await db.get(KnowledgeDocument, doc_id)
            data = lightrag_engine.get_graph_data(doc)
            if (not data.get("nodes")) and (not data.get("edges")):
                text = ""
                temp_path = None
                try:
                    if doc and doc.oss_key:
                        file_ext = os.path.splitext(doc.filename or "")[1] or ".txt"
                        temp_name = f"temp_graph_{doc.id}{file_ext}"
                        temp_path = UPLOAD_DIR / temp_name
                        storage_service.download_file(doc.oss_key, str(temp_path))
                        text = parse_local_file(str(temp_path))
                    else:
                        candidate = UPLOAD_DIR / (doc.filename or "")
                        if candidate.exists():
                            text = parse_local_file(str(candidate))
                except Exception:
                    pass
                finally:
                    if temp_path and os.path.exists(temp_path):
                        try:
                            os.remove(temp_path)
                        except Exception:
                            pass
                try:
                    res = await db.execute(
                        select(LLMModel)
                        .filter(LLMModel.is_active == True, LLMModel.model_type != "embedding")
                        .order_by(LLMModel.updated_at.desc())
                    )
                    llm_model = res.scalars().first()
                    if text and llm_model:
                        fallback = await self._extract_subgraph(text[:50000], llm_model)
                        if isinstance(fallback, dict) and (fallback.get("nodes") or fallback.get("edges")):
                            return fallback
                except Exception:
                    pass
            return data
        except Exception as e:
            logger.error(f"获取 LightRAG 图谱失败: {e}")
            return {"nodes": {}, "edges": {}, "reason": f"error:{str(e)}"}

    def _get_fallback_graph(self, filename: str) -> Dict[str, Any]:
        return {"nodes": {}, "edges": {}, "reason": "fallback_disabled"}


kb_service = KnowledgeBaseService.get_instance()
