from typing import List, Dict, Any, Optional
import time
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.knowledge_base import kb_service, UPLOAD_DIR
from app.models.knowledge import KnowledgeDocument, KnowledgeChat
from app.services.oss_service import oss_service
from pathlib import Path
import io
import PyPDF2
from app.services.lightrag_service import lightrag_service
from app.services.markdown import to_markdown

logger = logging.getLogger(__name__)

class QAService:
    """
    问答服务类，提供基于文档的混合检索问答功能。
    整合了 BM25 关键词检索、向量语义检索和知识图谱检索。
    """
    _instance = None

    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _read_document_content(self, doc: KnowledgeDocument) -> str:
        """
        读取文档内容，支持从本地或 OSS 获取。
        逻辑复用了 kb_service 中的部分代码，进行了简化。
        """
        filename = doc.filename or ""
        file_path = UPLOAD_DIR / filename
        raw_data = None

        # 1. 尝试从本地读取
        if not file_path.exists() and doc.oss_key:
             file_path = UPLOAD_DIR / Path(doc.oss_key).name
        
        if file_path.exists():
            try:
                raw_data = file_path.read_bytes()
            except Exception:
                pass

        # 2. 如果本地不存在，尝试从 OSS 读取
        if not raw_data and doc.oss_key:
            try:
                raw_data = oss_service.bucket.get_object(doc.oss_key).read()
            except Exception:
                pass
        
        if not raw_data:
            return ""

        text = ""
        file_ext = Path(filename).suffix.lower()
        
        try:
            # 3. 根据文件类型解析文本
            if file_ext == ".pdf":
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(raw_data))
                text = "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
            else:
                # 尝试多种编码格式解析文本
                for encoding in ['utf-8', 'gbk', 'gb18030', 'latin1']:
                    try:
                        text = raw_data.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                if not text:
                    text = raw_data.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"读取文档内容出错: {e}")
            return ""
            
        return to_markdown(text, {"source": "qa_read", "title": Path(filename).stem if filename else ""})

    async def graph_search(self, doc_id: int, query: str, db: AsyncSession, top_k: int = 5, trace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            graph_data = await kb_service.get_document_graph_local(db, doc_id)
            if not graph_data or "nodes" not in graph_data:
                logger.info(f"[QA][GRAPH][{trace_id}] empty graph for doc {doc_id}")
                return []
            nodes = graph_data.get("nodes") or {}
            edges = graph_data.get("edges") or {}
            q = (query or "").strip()
            results = []
            for node_id, node in nodes.items():
                name = str(node.get("name") or "")
                attrs = node.get("attributes") or {}
                score = 0
                if q and name and q in name:
                    score += 10
                for k, v in attrs.items():
                    s = str(v or "")
                    if q and s and q in s:
                        score += 2
                if score > 0:
                    content = f"实体: {name}\n属性: {attrs}\n"
                    results.append({"content": content, "score": float(score), "source": "graph"})
            for edge_id, edge in edges.items():
                label = str(edge.get("label") or "")
                s = 0
                if q and label and q in label:
                    s += 4
                if s > 0:
                    content = f"关系: {label} ({edge.get('source')} -> {edge.get('target')})\n"
                    results.append({"content": content, "score": float(s), "source": "graph"})
            results.sort(key=lambda x: x["score"], reverse=True)
            out = results[:top_k]
            logger.info(f"[QA][GRAPH][{trace_id}] doc {doc_id} qlen={len(q)} nodes={len(nodes)} edges={len(edges)} hits={len(out)}")
            return out
        except Exception:
            logger.exception(f"[QA][GRAPH][{trace_id}] graph search error for doc {doc_id}")
            return []

    async def _content_search(self, doc: KnowledgeDocument, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        text = self._read_document_content(doc)
        if not text or not (query or "").strip():
            return []
        chunks = self._chunk_text(text)
        if not chunks:
            return []
        q = (query or "").strip()
        results: List[Dict[str, Any]] = []
        for c in chunks:
            s = 0.0
            if q in c:
                s += 10.0
            try:
                # 简单覆盖度估计：查询字符是否出现在片段中
                overlap = sum(1 for ch in set(q) if ch in c)
                if overlap:
                    s += min(5.0, float(overlap))
            except Exception:
                pass
            if s > 0.0:
                results.append({"content": c[:400], "score": s})
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    async def qa(self, doc_id: int, query: str, db: AsyncSession, history: List[str] | None = None, trace_id: Optional[str] = None, scope: str = "doc") -> Dict[str, Any]:
        """
        主问答函数（LightRAG 方案）。
        直接使用 LightRAG 的混合检索与生成能力。
        """
        try:
            t0 = time.perf_counter()
            
            # Persist user message
            user_chat = KnowledgeChat(doc_id=doc_id, role="user", content=query)
            db.add(user_chat)
            await db.commit()

            await lightrag_service.ensure_initialized(db)
            logger.info(f"[QA][INIT][{trace_id}] ensured LightRAG in {time.perf_counter()-t0:.3f}s")
            
            # [Optimization] We now rely on LightRAG's internal retrieval for mode="mix"
            # No longer need manual retrieval which was causing double context injection.
            lightrag_service.clear_last_context()
            
            # If scope is "doc", we filter by doc_id. If "global", we don't.
            filter_doc_id = doc_id if scope == "doc" else None
            lightrag_service.set_runtime_vars(knowledge="", history=history, filter_doc_id=filter_doc_id)
            
            tq = time.perf_counter()
            answer = await lightrag_service.query_async(query, mode="mix", filter_doc_id=filter_doc_id)
            
            if not answer or not str(answer).strip() or "查询出错" in str(answer):
                logger.warning(f"[QA][GEN][{trace_id}] mix returned empty/error, fallback to local")
                alt = await lightrag_service.query_async(query, mode="local")
                answer = alt or answer
            if not answer or not str(answer).strip():
                answer = "未检索到有效答案"
            
            # [Refinement] Clean the answer text to remove raw document IDs and format citations
            answer_text = str(answer).strip()
            import re
            
            # 1. Handle in-text citations: [doc#3:xxx] -> [1] (if we can map it) or just remove the doc# part
            # But LightRAG usually uses [[Source: n]] or [n] for indexed sources.
            # If it uses raw doc# in text, we should clean it.
            answer_text = re.sub(r"doc#\d+:[a-f0-9-]+(\.\w+)?(:part\d+)?", "", answer_text)
            
            # 2. Remove the trailing "References" or "Sources" section
            # This is a very aggressive cleanup to ensure no raw reference lists appear.
            # We look for common reference headers and remove everything after them.
            answer_text = re.split(r"\n+\s*(?:#+\s*)?(?:\*\*)?(?:References|Sources|参考来源|引用|引用文献|Reference Document List)(?::|：)?(?:\*\*)?\s*(?:\n+|$)", answer_text, flags=re.IGNORECASE)[0]
            
            # 3. Also remove any trailing lines that look like [n] or [n] something
            lines = answer_text.split("\n")
            while lines and (re.match(r"^\s*\[\d+\]\s*.*$", lines[-1]) or not lines[-1].strip()):
                lines.pop()
            answer_text = "\n".join(lines)

            # 4. Trim multiple newlines and spaces
            answer_text = re.sub(r"\n{3,}", "\n\n", answer_text)
            answer_text = answer_text.strip()
            
            answer = answer_text
            
            # [Refinement] Extract sources from captured context and map doc IDs to filenames
            sources = []
            last_ctx = lightrag_service.get_last_context()
            if last_ctx:
                # 1. Chunks
                if "chunks" in last_ctx:
                    # LightRAG chunk list format: [n] Title \n Preview
                    chunk_matches = re.findall(r"\[(\d+)\]\s*(.*?)(?=\[\d+\]|$)", last_ctx["chunks"], re.DOTALL)
                    
                    # Pre-collect doc IDs to map filenames in bulk
                    doc_ids_to_fetch = set()
                    for _, ctext in chunk_matches:
                        dm = re.search(r"doc#(\d+)", ctext)
                        if dm:
                            doc_ids_to_fetch.add(int(dm.group(1)))
                    
                    doc_map = {}
                    if doc_ids_to_fetch:
                        res = await db.execute(select(KnowledgeDocument).filter(KnowledgeDocument.id.in_(doc_ids_to_fetch)))
                        doc_map = {d.id: d.filename for d in res.scalars().all()}

                    for cid, ctext in chunk_matches:
                        dm = re.search(r"doc#(\d+)", ctext)
                        did = int(dm.group(1)) if dm else None
                        fname = doc_map.get(did) if did else None
                        
                        sources.append({
                            "source": "vector", 
                            "id": int(cid),
                            "title": fname or ctext.strip().split("\n")[0][:50], # Filename as title
                            "content": ctext.strip(),
                            "score": 1.0
                        })
                
                # 2. Entities (Graph mapping)
                if "entities" in last_ctx:
                    try:
                        import json
                        ents = json.loads(last_ctx["entities"])
                        if isinstance(ents, list):
                            for ent in ents:
                                if isinstance(ent, dict):
                                    name = ent.get("entity_name") or ent.get("name")
                                    if name:
                                        sources.append({
                                            "source": "graph",
                                            "title": name,
                                            "content": f"实体: {name}\n类型: {ent.get('entity_type', 'Entity')}\n描述: {ent.get('description', '')}",
                                            "score": 1.0
                                        })
                    except Exception:
                        pass

            # Persist assistant message
            assistant_chat = KnowledgeChat(doc_id=doc_id, role="assistant", content=str(answer).strip(), sources=sources)
            db.add(assistant_chat)
            await db.commit()

            logger.info(f"[QA][DONE][{trace_id}] doc {doc_id} qlen={len(query or '')} sources={len(sources)} gen_time={time.perf_counter()-tq:.3f}s ans_len={len(str(answer) or '')}")
            return {"answer": str(answer).strip(), "sources": sources}
        except Exception as e:
            logger.error(f"LightRAG QA 失败: {e}")
            logger.exception(f"[QA][ERR][{trace_id}] doc {doc_id} q='{(query or '')[:80]}'")
            return {"answer": "抱歉，LightRAG 生成回答时遇到错误。", "sources": []}

qa_service = QAService.get_instance()
