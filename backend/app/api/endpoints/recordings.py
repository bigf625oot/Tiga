from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.db.session import get_db, AsyncSessionLocal
from app.models.recording import Recording
from app.services.s3_service import s3_service
from app.services.aliyun_asr_service import aliyun_asr_service
import uuid
import os
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

async def process_audio_background(recording_id: int, db_session_maker):
    """
    Background task to process audio with Aliyun ASR and (Mock) LLM
    """
    async with db_session_maker() as db:
        try:
            result = await db.execute(select(Recording).filter(Recording.id == recording_id))
            recording = result.scalars().first()
            if not recording:
                return

            # 1. Get Audio URL
            # Note: For Aliyun to work, this URL must be publicly accessible.
            # If running locally, you might need ngrok or use Mock mode (handled by service if keys missing)
            file_url = s3_service.generate_presigned_url(recording.s3_key)
            
            # If URL is local, warn user
            if "localhost" in file_url or "127.0.0.1" in file_url:
                logger.warning(f"Local URL detected: {file_url}. Aliyun ASR requires public URL.")
                # If we have keys, this will likely fail. 
                # If we don't have keys, the service falls back to Mock, so it's fine.
            
            # 2. Call ASR
            recording.asr_status = "processing"
            await db.commit()
            
            transcription = await aliyun_asr_service.transcribe_audio(file_url)
            
            if transcription:
                recording.transcription_text = transcription
                recording.asr_status = "completed"
                
                # 3. Call LLM Summary (Still Mock for now, or we can integrate LLM later)
                recording.summary_status = "processing"
                await db.commit()
                
                # Simple heuristic summary based on length
                if len(transcription) > 100:
                    recording.summary_text = f"【智能摘要】\n根据转写内容，主要包含以下要点：\n1. {transcription[:30]}...\n2. {transcription[30:60]}..."
                else:
                    recording.summary_text = "内容较短，无需摘要。"
                
                recording.summary_status = "completed"
                
                # 4. Recommendation (Mock)
                recording.recommendation_status = "processing"
                await db.commit()
                
                # Mock Recommendation
                recording.recommendation_text = f"【相关推荐】\n基于转写内容，为您推荐以下知识库文档：\n1. 《{recording.filename} 相关技术规范》\n2. 《语音识别最佳实践指南》\n3. 《会议记录归档流程》"
                recording.recommendation_status = "completed"
            else:
                 recording.transcription_text = "转写失败"
                 recording.summary_text = "转写失败，无法生成摘要"
                 recording.recommendation_text = "无法生成推荐"
                 recording.asr_status = "failed"
                 recording.summary_status = "failed"
                 recording.recommendation_status = "failed"

            await db.commit()
            
        except Exception as e:
            logger.error(f"Error processing recording {recording_id}: {e}")
            recording.asr_status = "failed"
            recording.summary_status = "failed"
            recording.recommendation_status = "failed"
            await db.commit()

@router.post("/folder")
async def create_folder(
    name: str,
    parent_id: int = None,
    db: AsyncSession = Depends(get_db)
):
    new_folder = Recording(
        filename=name,
        is_folder=True,
        parent_id=parent_id,
        format="folder",
        s3_key=None, # Folders don't have S3 content
        transcription_text="",
        summary_text=""
    )
    db.add(new_folder)
    await db.commit()
    await db.refresh(new_folder)
    return new_folder

@router.put("/{recording_id}/rename")
async def rename_recording(
    recording_id: int,
    name: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Recording).filter(Recording.id == recording_id))
    recording = result.scalars().first()
    if not recording:
        raise HTTPException(status_code=404, detail="Item not found")
        
    recording.filename = name
    await db.commit()
    await db.refresh(recording)
    return recording

@router.put("/{recording_id}/move")
async def move_recording(
    recording_id: int,
    target_parent_id: int = None, # None means root
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Recording).filter(Recording.id == recording_id))
    recording = result.scalars().first()
    if not recording:
        raise HTTPException(status_code=404, detail="Item not found")
        
    # Check if target folder exists (if not root)
    if target_parent_id is not None:
        target_result = await db.execute(select(Recording).filter(Recording.id == target_parent_id, Recording.is_folder == True))
        target_folder = target_result.scalars().first()
        if not target_folder:
             raise HTTPException(status_code=404, detail="Target folder not found")
             
    recording.parent_id = target_parent_id
    await db.commit()
    return {"status": "moved"}

@router.post("/upload")
async def upload_recording(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...), 
    duration: int = Form(0), 
    parent_id: int = Form(None), # Support upload to folder
    db: AsyncSession = Depends(get_db)
):
    # Generate unique key
    file_ext = os.path.splitext(file.filename)[1]
    s3_key = f"{uuid.uuid4()}{file_ext}"
    
    # Upload to S3
    success = await s3_service.upload_file(file.file, s3_key)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to upload file to S3")
    
    # Save metadata to DB
    new_recording = Recording(
        filename=file.filename,
        s3_key=s3_key,
        format=file_ext.replace(".", ""),
        duration=duration,
        file_size=file.size if file.size else 0,
        parent_id=parent_id,
        is_folder=False,
        upload_status="completed", # Upload is done at this point
        asr_status="pending",
        summary_status="pending",
        recommendation_status="pending",
        transcription_text="处理中...",
        summary_text="处理中...",
        recommendation_text="处理中..."
    )
    db.add(new_recording)
    await db.commit()
    await db.refresh(new_recording)
    
    # Trigger Background Task for ASR
    background_tasks.add_task(process_audio_background, new_recording.id, AsyncSessionLocal)

    return new_recording

@router.get("/")
async def list_recordings(
    parent_id: int = None, 
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db)
):
    query = select(Recording).filter(Recording.parent_id == parent_id).order_by(Recording.is_folder.desc(), Recording.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    recordings = result.scalars().all()
    return recordings

@router.get("/{recording_id}")
async def get_recording(recording_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Recording).filter(Recording.id == recording_id))
    recording = result.scalars().first()
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    # Generate Presigned URL for playback
    url = s3_service.generate_presigned_url(recording.s3_key)
    return {
        **recording.__dict__,
        "play_url": url
    }

@router.post("/{recording_id}/retry")
async def retry_transcription(
    recording_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Recording).filter(Recording.id == recording_id))
    recording = result.scalars().first()
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
        
    if recording.is_folder:
        raise HTTPException(status_code=400, detail="Cannot transcribe a folder")

    # Reset status
    recording.asr_status = "processing"
    recording.summary_status = "pending"
    recording.recommendation_status = "pending"
    recording.transcription_text = "重试处理中..."
    recording.summary_text = "重试处理中..."
    recording.recommendation_text = "重试处理中..."
    await db.commit()
    
    # Trigger Background Task
    background_tasks.add_task(process_audio_background, recording.id, AsyncSessionLocal)
    
    return {"status": "processing"}

@router.delete("/{recording_id}")
async def delete_recording(recording_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Recording).filter(Recording.id == recording_id))
    recording = result.scalars().first()
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    # Delete from S3 (Optional, maybe keep for backup)
    # s3_service.delete_file(recording.s3_key) 
    
    await db.delete(recording)
    await db.commit()
    return {"status": "deleted"}
