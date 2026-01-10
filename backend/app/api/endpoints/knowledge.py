from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import shutil
import os
import uuid
from pathlib import Path

from app.db.session import get_db, AsyncSessionLocal
from app.models.knowledge import KnowledgeDocument, DocumentStatus
from app.services.knowledge_base import kb_service, UPLOAD_DIR
from app.services.oss_service import oss_service
from app.services.graphiti_client import graphiti_client
from app.services.document_parser import parse_local_file

import logging

logger = logging.getLogger(__name__)

router = APIRouter()

async def background_upload_and_index(doc_id: int, temp_file_path: str, unique_filename: str):
    logger.info(f"Starting background processing for doc_id: {doc_id}")
    async with AsyncSessionLocal() as db:
        try:
            # Re-fetch doc
            result = await db.execute(select(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id))
            doc = result.scalars().first()
            if not doc:
                logger.warning(f"Document {doc_id} not found in DB")
                return

            # --- Step 1: Upload to OSS ---
            oss_key = f"knowledge/{unique_filename}"
            try:
                # Read from temp file
                with open(temp_file_path, "rb") as f:
                    file_content = f.read()
                
                oss_url = oss_service.upload_file(oss_key, file_content)
                
                doc.oss_key = oss_key
                doc.oss_url = oss_url
                doc.status = DocumentStatus.UPLOADED
                await db.commit()
                logger.info(f"Background OSS upload successful for {doc_id}")
            except Exception as e:
                doc.status = DocumentStatus.FAILED
                doc.error_message = f"OSS Upload Failed: {str(e)}"
                await db.commit()
                logger.error(f"Background OSS upload failed: {e}")
                return # Stop if upload fails

            # --- Step 2: Indexing (Vector) ---
            doc.status = DocumentStatus.INDEXING
            await db.commit()
            logger.info(f"Document {doc_id} status updated to INDEXING")
            
            try:
                # Use the same temp file for indexing
                logger.info(f"Indexing file at: {temp_file_path}")
                kb_service.index_document(temp_file_path)
                
                # --- Step 3: Graphiti Ingestion ---
                try:
                    text_content = parse_local_file(temp_file_path)
                    if text_content:
                        logger.info(f"Ingesting to Graphiti: {unique_filename}")
                        # Fire and forget / await
                        await graphiti_client.ingest_document(unique_filename, text_content)
                    else:
                        logger.warning(f"No text extracted for Graphiti ingestion: {unique_filename}")
                except Exception as ge:
                    logger.error(f"Graphiti ingestion failed: {ge}")
                    # Do not fail the whole process if Graphiti fails, as it might be optional
                
                doc.status = DocumentStatus.INDEXED
                logger.info(f"Document {doc_id} indexed successfully")
            except Exception as e:
                doc.status = DocumentStatus.FAILED
                doc.error_message = f"Indexing Failed: {str(e)}"
                logger.error(f"Failed to index document {doc_id}: {e}")
            
            await db.commit()

        except Exception as e:
            logger.error(f"Background processing error: {e}")
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
    
    # Use oss_key to identify the file in Graphiti
    # If oss_key is None, we can't find it in Graphiti (since we use unique_filename for ingest)
    if not doc.oss_key:
         return {"nodes": {}, "edges": {}}
         
    unique_filename = doc.oss_key.split("/")[-1]
    return await graphiti_client.get_document_graph(unique_filename)

