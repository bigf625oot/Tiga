import os
import shutil
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession


import logging

from app.db.session import AsyncSessionLocal, get_db
from app.models.knowledge import DocumentStatus, KnowledgeChat, KnowledgeDocument
from app.services.rag.parser import parse_local_file
from app.services.rag.knowledge_base import UPLOAD_DIR, kb_service
from app.services.rag.engines.lightrag import lightrag_engine
from app.services.storage.service import storage_service
from app.services.rag.qa import qa_service

logger = logging.getLogger(__name__)

router = APIRouter()


async def background_delete_cleanup(filename: str, oss_key: str = None):
    try:
        if oss_key:
            try:
                storage_service.delete_file(oss_key)
                logger.info(f"[BG] 已从OSS删除: {oss_key}")
            except Exception as e:
                logger.warning(f"[BG] 删除OSS对象失败: {e}")
        import asyncio

        try:
            await asyncio.to_thread(kb_service.delete_document, filename)
            logger.info(f"[BG] LightRAG清理完成: {filename}")
        except Exception as e:
            logger.warning(f"[BG] LightRAG清理失败 文件={filename}: {e}")
    except Exception as e:
        logger.error(f"[BG] 删除清理错误: {e}")


@router.post("/vector/clean")
async def clean_vector_store(db: AsyncSession = Depends(get_db)):
    await lightrag_engine.reset_vector_store(db)
    return {"status": "cleaned"}


@router.post("/vector/rebuild")
async def rebuild_vector_store(db: AsyncSession = Depends(get_db)):
    await lightrag_engine.rebuild_store(db)
    return {"status": "rebuilt"}


async def background_incremental_index(doc_id: int, segments: List[str]):
    try:
        async with AsyncSessionLocal() as db:
            await lightrag_engine.ensure_initialized(db)
        total = len(segments) + 1  # +1 for the first segment done in upload_and_index
        done = 1

        def get_stats():
            try:
                import networkx as nx

                from app.services.rag.engines.lightrag import LIGHTRAG_DIR

                p = LIGHTRAG_DIR / "graph_chunk_entity_relation.graphml"
                if not p.exists():
                    return 0, 0
                G = nx.read_graphml(str(p))
                return G.number_of_nodes(), G.number_of_edges()
            except:
                return 0, 0

        for i, seg in enumerate(segments):
            try:
                logger.info(f"[Async Incremental] Processing chunk {i + 1}/{len(segments)} (size={len(seg)})...")
                # Update status: Processing...
                async with AsyncSessionLocal() as db:
                    result = await db.execute(select(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id))
                    doc = result.scalars().first()
                    if doc:
                        doc.error_message = f"index_progress:{done}/{total} (processing part {done + 1}/{total})"
                        await db.commit()

                await lightrag_engine.insert_text_async(seg, description=f"doc#{doc_id}:part{done + 1}/{total}")
                done += 1

                # Update status: Done with part, show graph size
                n, e = get_stats()
                async with AsyncSessionLocal() as db:
                    try:
                        result = await db.execute(select(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id))
                        doc = result.scalars().first()
                        if doc:
                            doc.error_message = f"index_progress:{done}/{total} (graph: {n}n/{e}e)"
                            await db.commit()
                    except Exception:
                        pass
            except Exception:
                pass
        # Finalize: mark as indexed when all parts done
        async with AsyncSessionLocal() as db:
            try:
                result = await db.execute(select(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id))
                doc = result.scalars().first()
                if doc:
                    doc.status = DocumentStatus.INDEXED
                    doc.error_message = f"index_progress:{total}/{total}"
                    await db.commit()
            except Exception:
                pass
    except Exception:
        pass


async def background_upload_and_index(doc_id: int, temp_file_path: str, unique_filename: str):
    logger.info(f"开始后台处理 文档ID={doc_id}")

    # 辅助函数：更新文档状态（独立事务）
    async def update_doc_status(
        doc_id: int, status: DocumentStatus, error_msg: str = None, oss_key: str = None, oss_url: str = None
    ):
        async with AsyncSessionLocal() as db:
            try:
                result = await db.execute(select(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id))
                doc = result.scalars().first()
                if doc:
                    doc.status = status
                    if error_msg:
                        doc.error_message = error_msg
                    if oss_key:
                        doc.oss_key = oss_key
                    if oss_url:
                        doc.oss_url = oss_url
                    await db.commit()
                    logger.info(
                        f"文档状态更新 id={doc_id} 状态={status} 提示={error_msg} oss_key={getattr(doc, 'oss_key', None)} oss_url={getattr(doc, 'oss_url', None)}"
                    )
            except Exception as e:
                logger.error(f"更新文档状态失败: {e}")

    # 标记处理是否成功，用于决定是否清理临时文件
    process_success = False

    try:
        # --- Step 1: Upload to OSS ---
        oss_key = f"knowledge/{unique_filename}"
        oss_url = None
        try:
            logger.info(
                f"OSS上传前检查 路径={temp_file_path} 存在={os.path.exists(temp_file_path)} 大小={os.path.getsize(temp_file_path) if os.path.exists(temp_file_path) else 0}"
            )
            oss_url = storage_service.upload_file_path(oss_key, temp_file_path)
            await update_doc_status(doc_id, DocumentStatus.UPLOADED, error_msg=None, oss_key=oss_key, oss_url=oss_url)
            logger.info(f"OSS上传成功 文档ID={doc_id} 键={oss_key} URL={oss_url}")
        except Exception as e:
            logger.error(f"OSS上传失败: {e}", exc_info=True)
            await update_doc_status(doc_id, DocumentStatus.UPLOADING, error_msg=f"OSS 上传警告: {str(e)}")
            # 注意：OSS上传失败通常不应继续索引，但原逻辑似乎允许继续？
            # 如果OSS失败是致命的，这里应该raise或者return。
            # 暂时保持原逻辑结构，但要注意 process_success 最终可能为 True 如果索引成功了？
            # 通常如果OSS失败，后续索引可能也会有问题（如果依赖OSS），但这里索引是用本地文件的。

        # --- Step 2: Indexing via LightRAG ---
        await update_doc_status(doc_id, DocumentStatus.INDEXING)
        try:
            async with AsyncSessionLocal() as db:
                await lightrag_engine.ensure_initialized(db)
                result = await db.execute(select(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id))
                _doc = result.scalars().first()
                display_name = _doc.filename if _doc and _doc.filename else unique_filename
            exists = os.path.exists(temp_file_path)
            size = os.path.getsize(temp_file_path) if exists else 0
            logger.info(f"解析前检查 路径={temp_file_path} 存在={exists} 大小={size}")

            # [Optimization] Run parsing in thread pool to avoid blocking event loop
            import asyncio

            text = await asyncio.to_thread(parse_local_file, str(temp_file_path))

            logger.info(f"解析文本长度={len(text or '')}")
            if not text:
                raise RuntimeError("解析到的文本为空，无法索引")

            max_first = 5000  # [Optimization] Reduce first chunk size for faster feedback
            seg_size = 20000  # Smaller segments for more granular progress updates
            first = text[:max_first]
            rest = text[max_first:]

            segments = [rest[i : i + seg_size] for i in range(0, len(rest), seg_size)] if rest else []
            total = len(segments) + 1
            logger.info(
                f"[Document Processing] Chunking result: {total} parts (including first part). Seg size: {seg_size}"
            )

            # Initial status
            await update_doc_status(
                doc_id, DocumentStatus.INDEXING, error_msg=f"index_progress:0/{total} (正在提取图谱...)"
            )

            await lightrag_engine.insert_text_async(first, description=f"doc#{doc_id}:{display_name}")
            try:
                import networkx as nx

                from app.services.rag.engines.lightrag import LIGHTRAG_DIR

                gp = LIGHTRAG_DIR / "graph_chunk_entity_relation.graphml"
                if gp.exists():
                    G = nx.read_graphml(str(gp))
                    logger.info(
                        f"首段索引后图谱 节点={G.number_of_nodes()} 边={G.number_of_edges()} 文件大小={os.path.getsize(gp)}"
                    )
                else:
                    logger.info("首段索引后图谱文件缺失")
            except Exception as e:
                logger.warning(f"图谱检查失败: {e}")

            if segments:
                import asyncio

                try:
                    asyncio.create_task(background_incremental_index(doc_id, segments))
                except Exception:
                    await background_incremental_index(doc_id, segments)
            else:
                await update_doc_status(doc_id, DocumentStatus.INDEXED, error_msg=f"index_progress:{total}/{total}")

            logger.info(f"索引完成 文档ID={doc_id}")
            process_success = True  # 标记处理成功
        except Exception as e:
            import traceback

            error_trace = traceback.format_exc()
            logger.error(f"LightRAG 索引文档失败 id={doc_id}: {e}")
            logger.error(f"详细堆栈:\n{error_trace}")
            await update_doc_status(doc_id, DocumentStatus.FAILED, error_msg=f"LightRAG 索引失败: {str(e)}")

    except Exception as e:
        logger.error(f"后台处理错误: {e}", exc_info=True)
        await update_doc_status(doc_id, DocumentStatus.FAILED, error_msg=f"系统错误: {str(e)}")
    finally:
        # Cleanup Temp File
        # 只有在处理成功时才删除文件，失败时保留以便排查
        if process_success and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                logger.info(f"清理临时文件 路径={temp_file_path}")
            except Exception as e:
                logger.warning(f"清理临时文件失败 路径={temp_file_path}: {e}")
        elif not process_success and os.path.exists(temp_file_path):
            logger.warning(f"处理未完全成功，保留临时文件以供排查: {temp_file_path}")


@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)
):
    logger.info(f"收到上传请求 文件={file.filename}")
    # 1. Save to Temp File (for indexing)
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    temp_file_path = UPLOAD_DIR / unique_filename

    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        exists = os.path.exists(temp_file_path)
        size = os.path.getsize(temp_file_path) if exists else 0
        logger.info(f"已保存临时文件 路径={temp_file_path} 存在={exists} 大小={size}")

        # 2. Create DB Record (Initial status: UPLOADING)
        # Note: We rely on background task for OSS upload, so keys are None initially
        file_size = os.path.getsize(temp_file_path)

        new_doc = KnowledgeDocument(
            filename=file.filename, oss_key=None, oss_url=None, file_size=file_size, status=DocumentStatus.UPLOADING
        )
        db.add(new_doc)
        await db.commit()
        await db.refresh(new_doc)
        logger.info(f"已创建文档记录 id={new_doc.id} 文件名={new_doc.filename} 大小={file_size}")

        # 3. Trigger Background Task (OSS Upload + Indexing)
        background_tasks.add_task(background_upload_and_index, new_doc.id, str(temp_file_path), unique_filename)

        return new_doc

    except Exception as e:
        logger.error(f"上传初始化失败: {e}", exc_info=True)
        # Cleanup if failed
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_documents(db: AsyncSession = Depends(get_db)):
    logger.info("查询文档列表")
    result = await db.execute(select(KnowledgeDocument).order_by(KnowledgeDocument.created_at.desc()))
    docs = result.scalars().all()
    out = []

    def parse_progress(msg: str):
        try:
            if not msg:
                return None
            if "index_progress:" in msg:
                # 提取类似 "index_progress:1/3" 的部分
                main_part = msg.split("index_progress:")[-1].strip()
                # 取第一个空格前的部分，即 "1/3"
                ratio_part = main_part.split(" ")[0]
                nums = ratio_part.split("/")
                done = int(nums[0])
                total = int(nums[1]) if len(nums) > 1 else 0
                if total > 0:
                    return max(0, min(100, int(done * 100 / total)))
        except Exception:
            return None
        return None

    def status_text(s: DocumentStatus):
        try:
            if s == DocumentStatus.UPLOADING:
                return "上传中"
            if s == DocumentStatus.UPLOADED:
                return "已上传"
            if s == DocumentStatus.INDEXING:
                return "解析中"
            if s == DocumentStatus.INDEXED:
                return "已完成"
            if s == DocumentStatus.FAILED:
                return "失败"
        except Exception:
            pass
        return "未知"

    for d in docs:
        prog = parse_progress(d.error_message or "")
        try:
            out.append(
                {
                    "id": d.id,
                    "filename": d.filename,
                    "oss_key": d.oss_key,
                    "oss_url": d.oss_url,
                    "file_size": d.file_size,
                    "status": d.status,
                    "status_text": status_text(d.status),
                    "created_at": getattr(d, "created_at", None),
                    "updated_at": getattr(d, "updated_at", None),
                    "error_message": d.error_message,
                    "progress": prog,
                }
            )
        except Exception:
            pass
    return out


@router.delete("/{doc_id}")
async def delete_document(doc_id: int, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    logger.info(f"删除文档 {doc_id}")
    result = await db.execute(select(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id))
    doc = result.scalars().first()
    if not doc:
        logger.warning(f"文档 {doc_id} 未找到，无法删除")
        raise HTTPException(status_code=404, detail="Document not found")

    # Capture info for background cleanup
    filename = doc.filename
    oss_key = doc.oss_key
    # 1. Delete from DB (first)
    await db.delete(doc)
    await db.commit()
    logger.info(f"已从数据库删除文档 {doc_id}")

    # 2. Schedule background cleanup (OSS + LightRAG)
    try:
        background_tasks.add_task(background_delete_cleanup, filename, oss_key)
    except Exception as e:
        logger.warning(f"调度后台清理失败: {e}")
        # Best-effort immediate cleanup if scheduling fails
        try:
            await background_delete_cleanup(filename, oss_key)
        except Exception:
            pass

    return {"status": "deleted"}


@router.get("/{doc_id}/content")
async def get_document_content(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc = await db.get(KnowledgeDocument, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if not doc.oss_key:
        raise HTTPException(status_code=400, detail="Document has no file content (no OSS key)")

    temp_path = None
    try:
        # Download from OSS to temp file
        file_ext = os.path.splitext(doc.filename)[1]
        temp_filename = f"temp_download_{uuid.uuid4()}{file_ext}"
        temp_path = UPLOAD_DIR / temp_filename

        storage_service.download_file(doc.oss_key, str(temp_path))

        # Parse content
        content = parse_local_file(str(temp_path))

        return {"content": content, "filename": doc.filename}
    except Exception as e:
        logger.error(f"获取文档内容失败 id={doc_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve content: {str(e)}")
    finally:
        # Cleanup
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass


async def _enrich_graph_data(data: Dict[str, Any], db: AsyncSession):
    """辅助函数：将图谱中的 doc#ID 映射为真实文件名"""
    import re

    nodes = data.get("nodes") or {}
    if not nodes:
        return data

    # 收集所有需要查询的 doc_id
    doc_ids = set()
    for node in nodes.values():
        attrs = node.get("attributes") or {}
        fp = attrs.get("file_path") or ""
        match = re.search(r"doc#(\d+):", fp)
        if match:
            doc_ids.add(int(match.group(1)))

    if not doc_ids:
        return data

    # 批量查询文件名
    result = await db.execute(select(KnowledgeDocument).filter(KnowledgeDocument.id.in_(doc_ids)))
    doc_map = {d.id: d.filename for d in result.scalars().all()}

    # 更新节点属性
    for node in nodes.values():
        attrs = node.get("attributes") or {}
        fp = attrs.get("file_path") or ""

        # [Fix] 支持从多个文档来源提取文件名 (split by <SEP> first or regex all)
        # file_path format: doc#1:name1<SEP>doc#2:name2

        found_names = []
        matches = re.finditer(r"doc#(\d+):", fp)
        seen_dids = set()

        for match in matches:
            did = int(match.group(1))
            if did in doc_map and did not in seen_dids:
                found_names.append(doc_map[did])
                seen_dids.add(did)

        if found_names:
            # Join multiple filenames with comma or specific separator
            attrs["file_name"] = ", ".join(found_names)
            # 保留 file_path 以免破坏缓存数据，导致后续请求无法重新解析
            # if "file_path" in attrs:
            #     del attrs["file_path"]
            if "_file_path_raw" in attrs:
                del attrs["_file_path_raw"]
    return data


@router.get("/{doc_id}/graph")
async def get_document_graph(doc_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    doc = await db.get(KnowledgeDocument, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    local_graph = await kb_service.get_document_graph_local(db, doc_id)
    local_graph = await _enrich_graph_data(local_graph, db)

    try:
        tid = request.headers.get("X-Trace-Id") or str(uuid.uuid4())
        nodes = len(local_graph.get("nodes") or {})
        edges = len(local_graph.get("edges") or {})
        logger.info(f"[图谱][{tid}] 文档 {doc_id} 节点={nodes} 边={edges} 原因={local_graph.get('reason')}")
    except Exception:
        pass
    return local_graph


@router.get("/graph")
async def get_global_graph(request: Request, db: AsyncSession = Depends(get_db)):
    from app.services.rag.engines.lightrag import lightrag_engine

    await lightrag_engine.ensure_initialized(db)
    data = lightrag_engine.get_graph_data()
    data = await _enrich_graph_data(data, db)

    try:
        tid = request.headers.get("X-Trace-Id") or str(uuid.uuid4())
        nodes = len(data.get("nodes") or {})
        edges = len(data.get("edges") or {})
        logger.info(f"[图谱][{tid}] 全局 节点={nodes} 边={edges} 原因={data.get('reason')}")
    except Exception:
        pass
    return data


class QARequest(BaseModel):
    query: str
    history: Optional[List[str]] = None
    scope: str = "doc"  # "doc" or "global"
    session_id: Optional[str] = None


@router.get("/{doc_id}/qa/sessions")
async def list_doc_sessions(doc_id: int, db: AsyncSession = Depends(get_db)):
    """
    列出针对特定文档的所有会话列表。
    按时间倒序排列，包含最新一条消息预览。
    """
    from sqlalchemy import func

    # 1. 找出该文档下所有不为空的 session_id
    # 我们使用 group_by 来去重
    subquery = (
        select(
            KnowledgeChat.session_id,
            func.max(KnowledgeChat.created_at).label("last_active"),
            func.count(KnowledgeChat.id).label("msg_count"),
        )
        .where(KnowledgeChat.doc_id == doc_id)
        .where(KnowledgeChat.session_id != None)
        .group_by(KnowledgeChat.session_id)
        .order_by(func.max(KnowledgeChat.created_at).desc())
    )

    result = await db.execute(subquery)
    sessions = result.all()

    out = []
    for s in sessions:
        sid, last_ts, count = s

        # 获取该会话的最后一条消息作为预览
        # 优先取 User 的消息作为标题，如果没有则取 Assistant
        last_msg_stmt = (
            select(KnowledgeChat)
            .where(KnowledgeChat.session_id == sid)
            .order_by(KnowledgeChat.created_at.desc())
            .limit(1)
        )
        msg_res = await db.execute(last_msg_stmt)
        last_msg = msg_res.scalars().first()

        preview = ""
        if last_msg:
            preview = last_msg.content[:50] + "..." if len(last_msg.content) > 50 else last_msg.content

        out.append({"session_id": sid, "last_active": last_ts, "message_count": count, "preview": preview})

    return out


@router.delete("/{doc_id}/qa/history")
async def clear_qa_history(doc_id: int, session_id: str = Query(None), db: AsyncSession = Depends(get_db)):
    logger.info(f"清空文档 {doc_id} 的问答历史 (session_id={session_id})")
    try:
        query = delete(KnowledgeChat).where(KnowledgeChat.doc_id == doc_id)
        if session_id:
            query = query.where(KnowledgeChat.session_id == session_id)

        await db.execute(query)
        await db.commit()
        return {"status": "cleared"}
    except Exception as e:
        logger.error(f"清空问答历史失败: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{doc_id}/qa/history")
async def get_qa_history(doc_id: int, session_id: str = Query(None), db: AsyncSession = Depends(get_db)):
    logger.info(f"查询文档 {doc_id} 的问答历史 (session_id={session_id})")
    stmt = select(KnowledgeChat).filter(KnowledgeChat.doc_id == doc_id)
    if session_id:
        stmt = stmt.filter(KnowledgeChat.session_id == session_id)

    result = await db.execute(stmt.order_by(KnowledgeChat.created_at.asc()))
    history = result.scalars().all()
    logger.info(f"文档 {doc_id} 历史记录数量: {len(history)} (Session: {session_id})")
    return [
        {
            "role": h.role,
            "content": h.content,
            "sources": h.sources,
            "created_at": h.created_at,
            "session_id": getattr(h, "session_id", None),
        }
        for h in history
    ]


@router.post("/{doc_id}/qa")
async def document_qa(doc_id: int, request: QARequest, req: Request, db: AsyncSession = Depends(get_db)):
    tid = req.headers.get("X-Trace-Id") or str(uuid.uuid4())
    logger.info(
        f"[问答][{tid}] POST 文档 {doc_id} 范围={request.scope} 会话={request.session_id} 问句长度={len(request.query or '')}"
    )

    # 优先使用流式响应
    return StreamingResponse(
        qa_service.qa_stream(
            doc_id,
            request.query,
            db,
            history=request.history,
            trace_id=tid,
            scope=request.scope,
            session_id=request.session_id,
        ),
        media_type="text/plain",  # 或者 "text/event-stream"
    )


@router.get("/{doc_id}/qa")
async def document_qa_get(
    doc_id: int,
    q: str = Query(None),
    query: str = Query(None),
    history: str = Query(None),
    session_id: str = Query(None),
    req: Request = None,
    db: AsyncSession = Depends(get_db),
):
    qtext = q or query or ""
    if not qtext.strip():
        raise HTTPException(status_code=400, detail="缺少 query 参数")
    hist = [history] if history else None
    tid = (req.headers.get("X-Trace-Id") if req else None) or str(uuid.uuid4())
    logger.info(f"[问答][{tid}] GET 文档 {doc_id} 会话={session_id} 问句长度={len(qtext or '')}")
    return StreamingResponse(
        qa_service.qa_stream(doc_id, qtext, db, history=hist, trace_id=tid, session_id=session_id),
        media_type="text/plain",
    )


@router.post("/qa")
async def global_qa(request: QARequest, req: Request, db: AsyncSession = Depends(get_db)):
    tid = req.headers.get("X-Trace-Id") or str(uuid.uuid4())
    logger.info(
        f"[问答][{tid}] POST 全局 QA 范围={request.scope} 会话={request.session_id} 问句长度={len(request.query or '')}"
    )
    # Force global scope default if not provided, though QARequest default is "doc"
    scope = "global"
    # Pass doc_id=0 to indicate no specific document context
    return StreamingResponse(
        qa_service.qa_stream(
            0, request.query, db, history=request.history, trace_id=tid, scope=scope, session_id=request.session_id
        ),
        media_type="text/plain",
    )


# --- Chat History Management API ---


class MessageUpdate(BaseModel):
    content: Optional[str] = None
    role: Optional[str] = None


@router.delete("/chat/messages/{message_id}")
async def delete_chat_message(message_id: int, db: AsyncSession = Depends(get_db)):
    msg = await db.get(KnowledgeChat, message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    await db.delete(msg)
    await db.commit()
    return {"status": "deleted"}


@router.put("/chat/messages/{message_id}")
async def update_chat_message(message_id: int, update: MessageUpdate, db: AsyncSession = Depends(get_db)):
    msg = await db.get(KnowledgeChat, message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    if update.content is not None:
        msg.content = update.content
    if update.role is not None:
        msg.role = update.role

    await db.commit()
    await db.refresh(msg)
    return {
        "id": msg.id,
        "role": msg.role,
        "content": msg.content,
        "updated_at": msg.created_at,  # Actually should be updated_at if model has it
    }


@router.delete("/chat/sessions/{session_id}")
async def delete_chat_session(session_id: str, db: AsyncSession = Depends(get_db)):
    # Delete all messages with this session_id
    stmt = delete(KnowledgeChat).where(KnowledgeChat.session_id == session_id)
    result = await db.execute(stmt)
    await db.commit()
    return {"status": "deleted", "count": result.rowcount}
