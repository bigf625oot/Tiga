import io
import logging
import time
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import PyPDF2
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import KnowledgeChat, KnowledgeDocument
from app.services.rag.knowledge_base import UPLOAD_DIR, kb_service
from app.services.rag.engines.lightrag import lightrag_engine
from app.services.utils.markdown import to_markdown
from app.services.storage.service import storage_service

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
                # 优先尝试直接读取 (OSS legacy)
                if storage_service.bucket:
                     raw_data = storage_service.bucket.get_object(doc.oss_key).read()
                else:
                     # 下载到临时文件读取
                     temp_path = UPLOAD_DIR / f"temp_read_{doc.id}_{int(time.time())}"
                     storage_service.download_file(doc.oss_key, str(temp_path))
                     if temp_path.exists():
                         raw_data = temp_path.read_bytes()
                         try:
                             temp_path.unlink()
                         except:
                             pass
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
                for encoding in ["utf-8", "gbk", "gb18030", "latin1"]:
                    try:
                        text = raw_data.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                if not text:
                    text = raw_data.decode("utf-8", errors="ignore")
        except Exception as e:
            logger.error(f"读取文档内容出错: {e}")
            return ""

        return to_markdown(text, {"source": "qa_read", "title": Path(filename).stem if filename else ""})

    async def graph_search(
        self, doc_id: int, query: str, db: AsyncSession, top_k: int = 5, trace_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        try:
            graph_data = await kb_service.get_document_graph_local(db, doc_id)
            if not graph_data or "nodes" not in graph_data:
                logger.info(f"[QA][GRAPH][{trace_id}] empty graph for doc {doc_id}")
                return []
            nodes = graph_data.get("nodes") or {}
            edges = graph_data.get("edges") or {}
            q = (query or "").strip()
            results = []

            # 1. Keyword Search
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
                    results.append(
                        {"content": content, "score": float(score), "source": "graph_keyword", "id": node_id}
                    )

            # 2. Semantic Entity Search (Vector)
            # Find semantically similar entities in global store, then filter by current doc graph
            try:
                import asyncio
                vec_entities = await asyncio.to_thread(lightrag_engine.search_entities, q, top_k=20)
                for ve in vec_entities:
                    ename = ve.get("entity_name")
                    # Check if this entity exists in current doc's graph
                    if ename and ename in nodes:
                        # Avoid duplicates from keyword search
                        if not any(r.get("id") == ename for r in results):
                            node = nodes[ename]
                            attrs = node.get("attributes") or {}
                            # Base score 6 + vector score (usually 0-1)
                            v_score = 6.0 + ve.get("score", 0)
                            content = f"实体: {ename}\n属性: {attrs}\n"
                            results.append(
                                {"content": content, "score": v_score, "source": "graph_vector", "id": ename}
                            )
            except Exception as e:
                logger.warning(f"Graph vector search failed: {e}")

            for edge_id, edge in edges.items():
                label = str(edge.get("label") or "")
                s = 0
                if q and label and q in label:
                    s += 4
                if s > 0:
                    content = f"关系: {label} ({edge.get('source')} -> {edge.get('target')})\n"
                    results.append({"content": content, "score": float(s), "source": "graph_edge"})

            results.sort(key=lambda x: x["score"], reverse=True)

            # 3. [Fallback] If no keyword/vector match, return top degree nodes (important entities)
            # This handles generic queries like "Summarize this document" where no keywords match
            if not results and nodes:
                # Calculate degree for each node based on edges
                node_degrees = {nid: 0 for nid in nodes}
                for edge in edges.values():
                    s, t = edge.get("source"), edge.get("target")
                    if s in node_degrees:
                        node_degrees[s] += 1
                    if t in node_degrees:
                        node_degrees[t] += 1

                # Sort nodes by degree
                sorted_nodes = sorted(node_degrees.items(), key=lambda x: x[1], reverse=True)

                # Take top K nodes
                for nid, degree in sorted_nodes[:top_k]:
                    node = nodes[nid]
                    name = str(node.get("name") or "")
                    attrs = node.get("attributes") or {}
                    content = f"核心实体: {name}\n属性: {attrs}\n(重要性: {degree})"
                    results.append({"content": content, "score": 1.0, "source": "graph_rank"})

                logger.info(f"[QA][GRAPH][{trace_id}] fallback to top {len(results)} nodes by degree")

            out = results[:top_k]
            logger.info(
                f"[QA][GRAPH][{trace_id}] doc {doc_id} qlen={len(q)} nodes={len(nodes)} edges={len(edges)} hits={len(out)}"
            )
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
    
    def _chunk_text(self, text: str, chunk_size=400) -> List[str]:
        # Simple chunking for fallback
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    async def qa_stream(
        self,
        doc_id: int,
        query: str,
        db: Optional[AsyncSession] = None,
        history: Optional[List[str]] = None,
        trace_id: Optional[str] = None,
        scope: str = "doc",
        session_id: Optional[str] = None,
    ):
        """
        流式问答函数（支持过程展示）。
        通过 SSE 格式或纯文本流返回结果，包含检索过程。
        """
        from app.db.session import AsyncSessionLocal

        session = db
        should_close = False
        if not session:
            session = AsyncSessionLocal()
            should_close = True

        try:
            t0 = time.perf_counter()

            # 1. 初始思考过程
            yield "<think>\n"
            yield "正在初始化检索环境...\n"

            # 持久化用户消息
            try:
                user_chat = KnowledgeChat(doc_id=doc_id, role="user", content=query, session_id=session_id)
                session.add(user_chat)
                await session.commit()
            except Exception as e:
                logger.error(f"保存用户消息失败: {e}")

            await lightrag_engine.ensure_initialized(session)
            yield f"环境初始化完成 ({time.perf_counter() - t0:.3f}s)\n"

            # 清理上下文
            lightrag_engine.clear_last_context()

            # 设置运行时变量
            lightrag_engine.set_runtime_vars(knowledge="", history=history, filter_doc_id=None)

            yield f"正在执行混合检索 (Scope: {scope}, DocID: {doc_id if scope == 'doc' else 'Global'})...\n"

            # Context containers
            context_chunks = []
            context_entities = []

            import asyncio

            if scope == "doc":
                # Manual Document-Scoped Retrieval
                yield "正在进行文档专用向量检索...\n"
                raw_chunks = await asyncio.to_thread(lightrag_engine.search_doc_chunks, doc_id, query, top_k=15)

                # [Fallback] If vector search fails (e.g. generic query or empty index), read file head
                if not raw_chunks:
                    yield "向量检索未命中，尝试读取文档前文...\n"
                    try:
                        doc_obj = await session.get(KnowledgeDocument, doc_id)
                        if doc_obj:
                            import asyncio

                            content = await asyncio.to_thread(self._read_document_content, doc_obj)
                            if content:
                                raw_chunks.append(
                                    {
                                        "content": content[:8000],
                                        "file_path": f"doc#{doc_id}:{doc_obj.filename or 'Document'}",
                                        "score": 100.0,
                                    }
                                )
                    except Exception as e:
                        logger.warning(f"Fallback read failed: {e}")

                if raw_chunks:
                    yield f"找到 {len(raw_chunks)} 个相关文档片段：\n"
                    for i, c in enumerate(raw_chunks):
                        context_chunks.append(
                            {
                                "content": c.get("content", ""),
                                "file_path": c.get("file_path", ""),
                                "score": c.get("score", 0),
                            }
                        )
                        if i < 3:
                            preview = (c.get("content") or "").replace("\n", " ")[:50]
                            yield f"- [{i + 1}] {preview}...\n"
                else:
                    yield "向量检索未发现强相关片段，尝试图谱检索...\n"

                # Graph Search
                yield "正在进行文档专用图谱检索...\n"
                graph_results = await self.graph_search(doc_id, query, session, top_k=10)
                if graph_results:
                    yield f"找到 {len(graph_results)} 个相关实体/关系\n"
                    context_entities = graph_results

            else:
                # Global Scope (Legacy Logic)
                try:
                    yield "正在进行全局向量粗排...\n"
                    raw_chunks = await asyncio.to_thread(lightrag_engine.search_chunks, query, top_k=5)
                    if raw_chunks:
                        yield f"找到 {len(raw_chunks)} 个相关文档片段：\n"
                        for i, c in enumerate(raw_chunks):
                            preview = (c.get("preview") or "").replace("\n", " ")[:50]
                            yield f"- [{i + 1}] {preview}...\n"
                    else:
                        yield "向量检索未发现强相关片段，尝试图谱检索...\n"
                except Exception as e:
                    yield f"检索过程警告: {e}\n"

            tq = time.perf_counter()
            q_gen = f"{query} (请用中文回答)" if "中文" not in query else query

            yield "正在调用大模型生成回答...\n"
            yield "</think>\n"  # 结束思考/过程展示

            answer = ""

            if scope == "doc":
                # Manual Context Construction
                ctx_str = ""
                if context_chunks:
                    ctx_str += "Reference Document List\n"
                    for i, c in enumerate(context_chunks):
                        src = c.get("file_path") or f"doc#{doc_id}"
                        ctx_str += f"[{i + 1}] Source: {src}\n{c['content']}\n\n"

                if context_entities:
                    ctx_str += "####### Knowledge Graph Data (Entity)\n"
                    for e in context_entities:
                        ctx_str += f"{e['content']}\n"

                final_system_prompt = f"---Context---\n{ctx_str}\n"

                # Call LLM directly
                answer = await lightrag_engine.call_llm(q_gen, system_prompt=final_system_prompt)

            else:
                # Global Mode
                answer = await lightrag_engine.query_async(q_gen, mode="mix", filter_doc_id=None)

            # 处理结果
            fail_reason = None
            if not answer or not str(answer).strip() or "查询出错" in str(answer):
                fail_reason = "混合模式生成失败"
                alt = await lightrag_engine.query_async(q_gen, mode="local")
                answer = alt or answer
            else:
                s = str(answer)
                if any(x in s for x in ["[no-context]", "Authentication", "认证失败", "Sorry"]):
                    fail_reason = "触发敏感词屏蔽"
                    alt = await lightrag_engine.query_async(q_gen, mode="local")
                    answer = alt or answer

            answer_text = str(answer).strip()

            # 清理回答文本
            answer_text = re.sub(r"\[\[Source:\s*(\d+)\]\]", r"[\1]", answer_text)
            answer_text = re.sub(r"\[Source:\s*(\d+)\]", r"[\1]", answer_text)
            answer_text = re.sub(r"【(\d+)】", r"[\1]", answer_text)
            answer_text = re.split(
                r"(?:^|\n+)\s*(?:#+\s*)?(?:\*\*)?(?:References|Sources|参考来源|引用|引用文献|Reference Document List)(?::|：)?(?:\*\*)?\s*(?:\n+|$)",
                answer_text,
                flags=re.IGNORECASE,
            )[0]
            lines = answer_text.split("\n")
            while lines and (re.match(r"^\s*\[\d+\]\s*.*$", lines[-1]) or not lines[-1].strip()):
                lines.pop()
            answer_text = "\n".join(lines).strip()

            if not answer_text:
                answer_text = "未检索到有效答案"

            # 流式输出答案
            yield answer_text

            # 构建 Sources
            sources = []
            last_ctx = lightrag_engine.get_last_context()
            if last_ctx:
                # 1. Chunks
                chunks_text = last_ctx.get("chunks")
                if not chunks_text and last_ctx.get("raw"):
                    chunks_text = last_ctx.get("raw")
                    if "####### Knowledge Graph Data" in chunks_text:
                        chunks_text = chunks_text.split("####### Knowledge Graph Data")[0]

                if chunks_text:
                    chunk_matches = re.findall(r"\[(\d+)\]\s*(.*?)(?=\[\d+\]|$)", chunks_text, re.DOTALL)
                    doc_ids_to_fetch = set()
                    for _, ctext in chunk_matches:
                        dm = re.search(r"doc#(\d+)", ctext)
                        if dm:
                            doc_ids_to_fetch.add(int(dm.group(1)))

                    doc_map = {}
                    if doc_ids_to_fetch:
                        res = await session.execute(
                            select(KnowledgeDocument).filter(KnowledgeDocument.id.in_(doc_ids_to_fetch))
                        )
                        doc_map = {d.id: d.filename for d in res.scalars().all()}

                    for cid, ctext in chunk_matches:
                        dm = re.search(r"doc#(\d+)", ctext)
                        did = int(dm.group(1)) if dm else None
                        fname = doc_map.get(did) if did else None

                        sources.append(
                            {
                                "source": "vector",
                                "id": int(cid),
                                "title": fname or ctext.strip().split("\n")[0][:50],
                                "content": ctext.strip(),
                                "score": 1.0,
                                "doc_id": did,
                                "filename": fname,
                                "citation_index": int(cid),
                            }
                        )

                # 2. Entities
                if "entities" in last_ctx:
                    try:
                        ents = json.loads(last_ctx["entities"])
                        if isinstance(ents, list):
                            file_names_to_query = set()
                            for ent in ents:
                                if isinstance(ent, dict):
                                    name = ent.get("entity_name") or ent.get("name")
                                    etype = ent.get("entity_type")
                                    if name and etype in ["文件", "文档", "File", "Document"]:
                                        file_names_to_query.add(name)

                            name_to_id = {}
                            if file_names_to_query:
                                res = await session.execute(
                                    select(KnowledgeDocument).filter(
                                        KnowledgeDocument.filename.in_(file_names_to_query)
                                    )
                                )
                                for d in res.scalars().all():
                                    name_to_id[d.filename] = d.id

                            for ent in ents:
                                if isinstance(ent, dict):
                                    name = ent.get("entity_name") or ent.get("name")
                                    etype = ent.get("entity_type", "Entity")
                                    if name:
                                        src_item = {
                                            "source": "graph",
                                            "title": name,
                                            "content": f"实体: {name}\n类型: {etype}\n描述: {ent.get('description', '')}",
                                            "score": 1.0,
                                        }
                                        if etype in ["文件", "文档", "File", "Document"]:
                                            src_item["filename"] = name
                                            if name in name_to_id:
                                                src_item["doc_id"] = name_to_id[name]
                                        sources.append(src_item)
                    except Exception:
                        pass

            # 持久化助手消息
            try:
                assistant_chat = KnowledgeChat(
                    doc_id=doc_id, role="assistant", content=answer_text, sources=sources, session_id=session_id
                )
                session.add(assistant_chat)
                await session.commit()
            except Exception as e:
                logger.error(f"保存助手消息失败: {e}")

            # 输出引用来源
            if sources:
                yield "\n\n**知识来源：**\n"
                seen_titles = set()
                for s in sources:
                    t = s.get("title") or "未知来源"
                    idx = s.get("citation_index")
                    prefix = f"[{idx}] " if idx else "- "

                    if not idx and t in seen_titles:
                        continue
                    seen_titles.add(t)

                    yield f"{prefix}{t}\n"

        except Exception as e:
            logger.error(f"LightRAG QA Stream 失败: {e}")
            import traceback

            logger.error(traceback.format_exc())
            yield f"\n[Error] 生成回答时遇到错误: {str(e)}"
        finally:
            if should_close and session:
                await session.close()

    async def qa(
        self,
        doc_id: int,
        query: str,
        db: AsyncSession,
        history: Optional[List[str]] = None,
        trace_id: Optional[str] = None,
        scope: str = "doc",
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        主问答函数（LightRAG 方案）。
        直接使用 LightRAG 的混合检索与生成能力。
        """
        try:
            t0 = time.perf_counter()

            # 持久化用户消息
            user_chat = KnowledgeChat(doc_id=doc_id, role="user", content=query, session_id=session_id)
            db.add(user_chat)
            await db.commit()

            await lightrag_engine.ensure_initialized(db)
            logger.info(f"[QA][INIT][{trace_id}] ensured LightRAG in {time.perf_counter() - t0:.3f}s")

            lightrag_engine.clear_last_context()

            filter_doc_id = doc_id if scope == "doc" else None
            lightrag_engine.set_runtime_vars(knowledge="", history=history, filter_doc_id=filter_doc_id)

            tq = time.perf_counter()
            q_gen = f"{query} (请用中文回答)" if "中文" not in query else query

            answer = await lightrag_engine.query_async(q_gen, mode="mix", filter_doc_id=filter_doc_id)
            logger.info(f"[QA][RAW][{trace_id}] answer len={len(str(answer)) if answer else 0}: {str(answer)[:200]}...")

            fail_reason = None
            if not answer or not str(answer).strip() or "查询出错" in str(answer):
                fail_reason = "混合模式生成失败"
                alt = await lightrag_engine.query_async(q_gen, mode="local")
                answer = alt or answer
            else:
                s = str(answer)
                if any(x in s for x in ["[no-context]", "Authentication", "认证失败", "Sorry"]):
                    fail_reason = "触发敏感词屏蔽"
                    alt = await lightrag_engine.query_async(q_gen, mode="local")
                    answer = alt or answer

            invalid = (
                not answer
                or not str(answer).strip()
                or any(x in str(answer) for x in ["[no-context]", "Authentication", "认证失败", "Sorry"])
            )
            if invalid and not fail_reason:
                fail_reason = "本地模式生成无效"

            sources = []
            if invalid:
                logger.info(f"[QA][FALLBACK][{trace_id}] answer invalid (reason={fail_reason}), trying vector chunks")
                previews = []
                import asyncio
                vec_refs = await asyncio.to_thread(lightrag_engine.search_chunks, query, top_k=5)
                if vec_refs:
                    previews = [r.get("preview") or "" for r in vec_refs if r.get("preview")]
                    previews = [p.strip() for p in previews if p.strip()]
                    if previews:
                        answer = "以下是与问题相关的文档片段整理：\n\n" + "\n\n".join(previews[:3])
                        sources = [
                            {
                                "source": "vector",
                                "title": r.get("title") or "",
                                "content": r.get("preview") or "",
                                "score": r.get("score") or 0.0,
                            }
                            for r in vec_refs[:3]
                        ]
                        fail_reason = "向量补救成功"
                if not previews:
                    fail_reason = fail_reason or "向量检索无结果"
                    answer = "未检索到有效答案"
            if not answer or not str(answer).strip():
                fail_reason = fail_reason or "最终结果为空"
                answer = "未检索到有效答案"

            answer_text = str(answer).strip()
            
            # 清理回答
            answer_text = re.sub(r"\[\[Source:\s*(\d+)\]\]", r"[\1]", answer_text)
            answer_text = re.sub(r"\[Source:\s*(\d+)\]", r"[\1]", answer_text)
            answer_text = re.sub(r"【(\d+)】", r"[\1]", answer_text)
            answer_text = re.split(
                r"(?:^|\n+)\s*(?:#+\s*)?(?:\*\*)?(?:References|Sources|参考来源|引用|引用文献|Reference Document List)(?::|：)?(?:\*\*)?\s*(?:\n+|$)",
                answer_text,
                flags=re.IGNORECASE,
            )[0]
            lines = answer_text.split("\n")
            while lines and (re.match(r"^\s*\[\d+\]\s*.*$", lines[-1]) or not lines[-1].strip()):
                lines.pop()
            answer_text = "\n".join(lines).strip()
            answer_text = re.sub(r"\n{3,}", "\n\n", answer_text)
            
            answer = answer_text
            if not answer:
                 answer = "未检索到有效答案"

            # 提取 Sources (与 qa_stream 类似，复用 last_context)
            last_ctx = lightrag_engine.get_last_context()
            if last_ctx:
                chunks_text = last_ctx.get("chunks")
                if not chunks_text and last_ctx.get("raw"):
                    chunks_text = last_ctx.get("raw")
                    if "####### Knowledge Graph Data" in chunks_text:
                        chunks_text = chunks_text.split("####### Knowledge Graph Data")[0]

                if chunks_text:
                    chunk_matches = re.findall(r"\[(\d+)\]\s*(.*?)(?=\[\d+\]|$)", chunks_text, re.DOTALL)
                    doc_ids_to_fetch = set()
                    for _, ctext in chunk_matches:
                        dm = re.search(r"doc#(\d+)", ctext)
                        if dm:
                            doc_ids_to_fetch.add(int(dm.group(1)))

                    doc_map = {}
                    if doc_ids_to_fetch:
                        res = await db.execute(
                            select(KnowledgeDocument).filter(KnowledgeDocument.id.in_(doc_ids_to_fetch))
                        )
                        doc_map = {d.id: d.filename for d in res.scalars().all()}

                    for cid, ctext in chunk_matches:
                        dm = re.search(r"doc#(\d+)", ctext)
                        did = int(dm.group(1)) if dm else None
                        fname = doc_map.get(did) if did else None

                        sources.append(
                            {
                                "source": "vector",
                                "id": int(cid),
                                "title": fname or ctext.strip().split("\n")[0][:50],
                                "content": ctext.strip(),
                                "score": 1.0,
                                "doc_id": did,
                                "filename": fname,
                                "citation_index": int(cid),
                            }
                        )
                
                if "entities" in last_ctx:
                    try:
                        ents = json.loads(last_ctx["entities"])
                        if isinstance(ents, list):
                            for ent in ents:
                                if isinstance(ent, dict):
                                    name = ent.get("entity_name") or ent.get("name")
                                    etype = ent.get("entity_type", "Entity")
                                    if name:
                                        src_item = {
                                            "source": "graph",
                                            "title": name,
                                            "content": f"实体: {name}\n类型: {etype}\n描述: {ent.get('description', '')}",
                                            "score": 1.0,
                                        }
                                        sources.append(src_item)
                    except Exception:
                        pass

            assistant_chat = KnowledgeChat(
                doc_id=doc_id, role="assistant", content=str(answer).strip(), sources=sources, session_id=session_id
            )
            db.add(assistant_chat)
            await db.commit()

            logger.info(
                f"[QA][DONE][{trace_id}] doc {doc_id} qlen={len(query or '')} sources={len(sources)} gen_time={time.perf_counter() - tq:.3f}s ans_len={len(str(answer) or '')} reason={fail_reason}"
            )
            return {"answer": str(answer).strip(), "sources": sources, "reason": fail_reason}
        except Exception as e:
            logger.error(f"LightRAG QA 失败: {e}")
            logger.exception(f"[QA][ERR][{trace_id}] doc {doc_id} q='{(query or '')[:80]}'")
            return {"answer": "抱歉，LightRAG 生成回答时遇到错误。", "sources": []}


qa_service = QAService.get_instance()
