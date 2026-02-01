from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List, Dict, Any
import shutil
import os
import uuid
from pathlib import Path
from pydantic import BaseModel

from app.db.session import get_db, AsyncSessionLocal
from app.models.knowledge import KnowledgeDocument, DocumentStatus, KnowledgeChat
from app.services.knowledge_base import kb_service, UPLOAD_DIR
from app.services.oss_service import oss_service
from app.services.document_parser import parse_local_file
from app.services.lightrag_service import lightrag_service

import logging
from app.services.qa_service import qa_service

logger = logging.getLogger(__name__)

router = APIRouter()

async def background_delete_cleanup(filename: str, oss_key: str = None):
    try:
        if oss_key:
            try:
                oss_service.delete_file(oss_key)
                logger.info(f"[BG] Deleted from OSS: {oss_key}")
            except Exception as e:
                logger.warning(f"[BG] Failed to delete from OSS: {e}")
        import asyncio
        try:
            await asyncio.to_thread(kb_service.delete_document, filename)
            logger.info(f"[BG] LightRAG cleanup done for: {filename}")
        except Exception as e:
            logger.warning(f"[BG] LightRAG cleanup failed for {filename}: {e}")
    except Exception as e:
        logger.error(f"[BG] Delete cleanup error: {e}")

@router.post("/vector/clean")
async def clean_vector_store(db: AsyncSession = Depends(get_db)):
    await lightrag_service.reset_vector_store(db)
    return {"status": "cleaned"}

@router.post("/vector/rebuild")
async def rebuild_vector_store(db: AsyncSession = Depends(get_db)):
    await lightrag_service.rebuild_store(db)
    return {"status": "rebuilt"}

async def background_incremental_index(doc_id: int, segments: List[str]):
    try:
        async with AsyncSessionLocal() as db:
            await lightrag_service.ensure_initialized(db)
        total = len(segments) + 1 # +1 for the first segment done in upload_and_index
        done = 1
        
        def get_stats():
            try:
                from app.services.lightrag_service import LIGHTRAG_DIR
                import networkx as nx
                p = LIGHTRAG_DIR / "graph_chunk_entity_relation.graphml"
                if not p.exists(): return 0, 0
                G = nx.read_graphml(str(p))
                return G.number_of_nodes(), G.number_of_edges()
            except: return 0, 0

        for i, seg in enumerate(segments):
            try:
                # Update status: Processing...
                async with AsyncSessionLocal() as db:
                    result = await db.execute(select(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id))
                    doc = result.scalars().first()
                    if doc:
                        doc.error_message = f"index_progress:{done}/{total} (processing part {done+1}/{total})"
                        await db.commit()

                await lightrag_service.insert_text_async(seg, description=f"doc#{doc_id}:part{done+1}/{total}")
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
    except Exception:
        pass

async def background_upload_and_index(doc_id: int, temp_file_path: str, unique_filename: str):
    logger.info(f"Starting background processing for doc_id: {doc_id}")
    
    # 辅助函数：更新文档状态（独立事务）
    async def update_doc_status(doc_id: int, status: DocumentStatus, error_msg: str = None, 
                                oss_key: str = None, oss_url: str = None):
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
                    logger.info(f"Updated doc {doc_id} status to {status}")
            except Exception as e:
                logger.error(f"Failed to update doc status: {e}")

    try:
        # --- Step 1: Upload to OSS ---
        oss_key = f"knowledge/{unique_filename}"
        oss_url = None
        try:
            oss_url = oss_service.upload_file_path(oss_key, temp_file_path)
            await update_doc_status(doc_id, DocumentStatus.UPLOADED, oss_key=oss_key, oss_url=oss_url)
            logger.info(f"Background OSS upload successful for {doc_id}")
        except Exception as e:
            logger.error(f"Background OSS upload failed: {e}")
            await update_doc_status(doc_id, DocumentStatus.UPLOADING, error_msg=f"OSS Upload Warning: {str(e)}")


        # --- Step 2: Indexing via LightRAG ---
        await update_doc_status(doc_id, DocumentStatus.INDEXING)
        try:
            async with AsyncSessionLocal() as db:
                await lightrag_service.ensure_initialized(db)
            text = parse_local_file(str(temp_file_path))
            if not text:
                raise RuntimeError("解析到的文本为空，无法索引")
            
            max_first = 200000
            seg_size = 200000
            first = text[:max_first]
            rest = text[max_first:]
            
            segments = [rest[i:i+seg_size] for i in range(0, len(rest), seg_size)] if rest else []
            total = len(segments) + 1
            
            # Initial status
            await update_doc_status(doc_id, DocumentStatus.INDEXING, error_msg=f"index_progress:0/{total} (extracting graph...)")
            
            await lightrag_service.insert_text_async(first, description=f"doc#{doc_id}:{unique_filename}:part1")
            
            if segments:
                import asyncio
                try:
                    asyncio.create_task(background_incremental_index(doc_id, segments))
                except Exception:
                    await background_incremental_index(doc_id, segments)
            else:
                await update_doc_status(doc_id, DocumentStatus.INDEXED, error_msg=f"index_progress:{total}/{total}")
            
            logger.info(f"Document {doc_id} indexed into LightRAG successfully")
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"Failed to LightRAG index document {doc_id}: {e}")
            logger.error(f"Detailed Traceback:\n{error_trace}")
            await update_doc_status(doc_id, DocumentStatus.FAILED, error_msg=f"LightRAG Indexing Failed: {str(e)}")

        
    except Exception as e:
        logger.error(f"Background processing error: {e}")
        await update_doc_status(doc_id, DocumentStatus.FAILED, error_msg=f"System Error: {str(e)}")
    finally:
         # Cleanup Temp File
         if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                logger.info(f"Cleaned up temp file: {temp_file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp file {temp_file_path}: {e}")

@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"Received upload request for file: {file.filename}")
    # 1. Save to Temp File (for indexing)
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    temp_file_path = UPLOAD_DIR / unique_filename
    
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"Saved temp file to: {temp_file_path}")
        
        # 2. Create DB Record (Initial status: UPLOADING)
        # Note: We rely on background task for OSS upload, so keys are None initially
        file_size = os.path.getsize(temp_file_path)
        
        new_doc = KnowledgeDocument(
            filename=file.filename,
            oss_key=None,
            oss_url=None,
            file_size=file_size,
            status=DocumentStatus.UPLOADING
        )
        db.add(new_doc)
        await db.commit()
        await db.refresh(new_doc)
        logger.info(f"Created DB record for doc_id: {new_doc.id}")
        
        # 3. Trigger Background Task (OSS Upload + Indexing)
        background_tasks.add_task(background_upload_and_index, new_doc.id, str(temp_file_path), unique_filename)
        
        return new_doc
        
    except Exception as e:
        logger.error(f"Upload init failed: {e}")
        # Cleanup if failed
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_documents(db: AsyncSession = Depends(get_db)):
    logger.info("Listing documents")
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
            out.append({
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
                "progress": prog
            })
        except Exception:
            pass
    return out

@router.delete("/{doc_id}")
async def delete_document(doc_id: int, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    logger.info(f"Deleting document {doc_id}")
    result = await db.execute(select(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id))
    doc = result.scalars().first()
    if not doc:
        logger.warning(f"Document {doc_id} not found for deletion")
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Capture info for background cleanup
    filename = doc.filename
    oss_key = doc.oss_key
    # 1. Delete from DB (first)
    await db.delete(doc)
    await db.commit()
    logger.info(f"Deleted document {doc_id} from DB")
    
    # 2. Schedule background cleanup (OSS + LightRAG)
    try:
        background_tasks.add_task(background_delete_cleanup, filename, oss_key)
    except Exception as e:
        logger.warning(f"Failed to schedule background cleanup: {e}")
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
        
        oss_service.download_file(doc.oss_key, str(temp_path))
        
        # Parse content
        content = parse_local_file(str(temp_path))
        
        return {"content": content, "filename": doc.filename}
    except Exception as e:
        logger.error(f"Failed to retrieve content for doc {doc_id}: {e}")
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
        match = re.search(r"doc#(\d+):", fp)
        if match:
            did = int(match.group(1))
            if did in doc_map:
                # 只保留一个清晰的文件名展示，删除冗余的 file_path
                attrs["file_name"] = doc_map[did]
                if "file_path" in attrs:
                    del attrs["file_path"]
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
        logger.info(f"[GRAPH][{tid}] doc {doc_id} nodes={nodes} edges={edges} reason={local_graph.get('reason')}")
    except Exception:
        pass
    return local_graph

@router.get("/graph")
async def get_global_graph(request: Request, db: AsyncSession = Depends(get_db)):
    from app.services.lightrag_service import lightrag_service
    await lightrag_service.ensure_initialized(db)
    data = lightrag_service.get_graph_data()
    data = await _enrich_graph_data(data, db)
    
    try:
        tid = request.headers.get("X-Trace-Id") or str(uuid.uuid4())
        nodes = len(data.get("nodes") or {})
        edges = len(data.get("edges") or {})
        logger.info(f"[GRAPH][{tid}] global nodes={nodes} edges={edges} reason={data.get('reason')}")
    except Exception:
        pass
    return data

class QARequest(BaseModel):
    query: str
    history: List[str] | None = None
    scope: str = "doc" # "doc" or "global"

@router.delete("/{doc_id}/qa/history")
async def clear_qa_history(doc_id: int, db: AsyncSession = Depends(get_db)):
    logger.info(f"Clearing QA history for doc {doc_id}")
    try:
        await db.execute(
            delete(KnowledgeChat)
            .where(KnowledgeChat.doc_id == doc_id)
        )
        await db.commit()
        return {"status": "cleared"}
    except Exception as e:
        logger.error(f"Failed to clear QA history: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{doc_id}/qa/history")
async def get_qa_history(doc_id: int, db: AsyncSession = Depends(get_db)):
    logger.info(f"Fetching QA history for doc {doc_id}")
    result = await db.execute(
        select(KnowledgeChat)
        .filter(KnowledgeChat.doc_id == doc_id)
        .order_by(KnowledgeChat.created_at.asc())
    )
    history = result.scalars().all()
    return [
        {
            "role": h.role,
            "content": h.content,
            "sources": h.sources,
            "created_at": h.created_at
        }
        for h in history
    ]

@router.post("/{doc_id}/qa")
async def document_qa(doc_id: int, request: QARequest, req: Request, db: AsyncSession = Depends(get_db)):
    tid = req.headers.get("X-Trace-Id") or str(uuid.uuid4())
    logger.info(f"[QA][{tid}] POST doc {doc_id} scope={request.scope} qlen={len(request.query or '')}")
    return await qa_service.qa(doc_id, request.query, db, history=request.history, trace_id=tid, scope=request.scope)

@router.get("/{doc_id}/qa")
async def document_qa_get(doc_id: int, q: str = Query(None), query: str = Query(None), history: str = Query(None), req: Request = None, db: AsyncSession = Depends(get_db)):
    qtext = q or query or ""
    if not qtext.strip():
        raise HTTPException(status_code=400, detail="缺少 query 参数")
    hist = [history] if history else None
    tid = (req.headers.get("X-Trace-Id") if req else None) or str(uuid.uuid4())
    logger.info(f"[QA][{tid}] GET doc {doc_id} qlen={len(qtext or '')}")
    return await qa_service.qa(doc_id, qtext, db, history=hist, trace_id=tid)
