from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import shutil
import os
import uuid
from pathlib import Path
from pydantic import BaseModel

from app.db.session import get_db, AsyncSessionLocal
from app.models.knowledge import KnowledgeDocument, DocumentStatus
from app.services.knowledge_base import kb_service, UPLOAD_DIR
from app.services.oss_service import oss_service
from app.services.document_parser import parse_local_file
from app.services.lightrag_service import lightrag_service

import logging
from app.services.qa_service import qa_service

logger = logging.getLogger(__name__)

router = APIRouter()

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
            # [HOTFIX] OSS 失败不应阻塞本地解析
            # 如果 OSS 配置不正确或网络问题，我们仍然希望本地功能（向量检索、图谱）可用
            # 所以这里记录错误，但不返回，继续执行 Step 2
            # 仅更新错误信息，状态仍为 UPLOADING (或者可以引入一个 PARTIAL_FAILED 状态，这里暂用警告)
            await update_doc_status(doc_id, DocumentStatus.UPLOADING, error_msg=f"OSS Upload Warning: {str(e)}")
            # 继续往下执行...


        # --- Step 2: Indexing (Vector) ---
        await update_doc_status(doc_id, DocumentStatus.INDEXING)
        
        # Ensure LightRAG is initialized with DB config
        # Use a short-lived session just for config loading
        async with AsyncSessionLocal() as db:
            logger.info(f"Initializing LightRAG for doc_id: {doc_id}")
            await lightrag_service.ensure_initialized(db)
        
        try:
            # Use the same temp file for indexing
            logger.info(f"Starting Vector Indexing for: {temp_file_path}")
            # Run in thread pool to avoid blocking async loop
            import asyncio
            # [CRITICAL] 确保 kb_service.index_document 正确处理异常并打印详细日志
            # 由于这可能耗时较长，我们不设置超时，或者设置一个较长的超时
            await asyncio.to_thread(kb_service.index_document, temp_file_path)
            logger.info(f"Vector Indexing completed for: {temp_file_path}")
            
            # --- Step 3: Pre-calculate Local Graph (Async) ---
            logger.info(f"Starting background local graph generation for {doc_id} (FORCE REFRESH)...")
            # We need a db session here just for graph retrieval/caching if needed, 
            # though kb_service.get_document_graph_local mostly reads from disk/lightrag.
            # But let's follow the signature.
            async with AsyncSessionLocal() as db:
                await kb_service.get_document_graph_local(db, doc_id, force_refresh=True)
            logger.info(f"Background local graph generation completed for {doc_id}")
            
            await update_doc_status(doc_id, DocumentStatus.INDEXED)
            logger.info(f"Document {doc_id} indexed successfully")
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"Failed to index document {doc_id}: {e}")
            logger.error(f"Detailed Traceback:\n{error_trace}")
            
            # Mark as FAILED only if it's a hard failure
            await update_doc_status(doc_id, DocumentStatus.FAILED, error_msg=f"Indexing Failed: {str(e)}")
        
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
    return result.scalars().all()

@router.delete("/{doc_id}")
async def delete_document(doc_id: int, db: AsyncSession = Depends(get_db)):
    logger.info(f"Deleting document {doc_id}")
    result = await db.execute(select(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id))
    doc = result.scalars().first()
    if not doc:
        logger.warning(f"Document {doc_id} not found for deletion")
        raise HTTPException(status_code=404, detail="Document not found")
    
    # 1. Delete from OSS
    if doc.oss_key:
        try:
            oss_service.delete_file(doc.oss_key)
            logger.info(f"Deleted from OSS: {doc.oss_key}")
        except Exception as e:
            logger.error(f"Failed to delete from OSS: {e}")
    
    # 2. Delete from Vector DB
    try:
        kb_service.delete_document(doc.filename)
        logger.info(f"Deleted from Vector DB: {doc.filename}")
    except Exception as e:
        logger.error(f"Failed to delete from Vector DB: {e}")
    
    # 3. Delete from DB
    await db.delete(doc)
    await db.commit()
    logger.info(f"Deleted document {doc_id} from DB")
    
    return {"status": "deleted"}

@router.get("/{doc_id}/graph")
async def get_document_graph(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc = await db.get(KnowledgeDocument, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # 1. Check if graph exists in cache (Fast Path)
    # The background task should have populated this.
    local_graph = await kb_service.get_document_graph_local(db, doc_id)
    
    # If empty, it might mean:
    # a) Background task hasn't finished yet
    # b) Extraction failed
    # c) Document is empty
    # Ideally we should return a status to frontend, but for now we just return what we have.
    # If it's empty, frontend shows "No Data".
    
    if local_graph and local_graph.get("nodes"):
        return local_graph
    
    # Fallback to Graphiti (Legacy path) - Removed
    
    return {"nodes": {}, "edges": {}}

class QARequest(BaseModel):
    query: str

@router.post("/{doc_id}/qa")
async def document_qa(doc_id: int, request: QARequest, db: AsyncSession = Depends(get_db)):
    return await qa_service.qa(doc_id, request.query, db)
