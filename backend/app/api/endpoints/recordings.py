import logging
import os
import uuid
import shutil
import tempfile
import json
from pydub import AudioSegment
import imageio_ffmpeg

# Configure pydub to use imageio-ffmpeg
AudioSegment.converter = imageio_ffmpeg.get_ffmpeg_exe()

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

from app.db.session import AsyncSessionLocal, get_db
from app.models.recording import Recording
from app.models.llm_model import LLMModel
from app.services.media.asr import aliyun_asr_service
from app.services.storage.service import storage_service
from app.services.llm.factory import ModelFactory
from app.services.rag.engines.lightrag import lightrag_engine
from agno.agent import Agent

logger = logging.getLogger(__name__)

router = APIRouter()


async def process_audio_background(recording_id: int, db_session_maker):
    """
    Background task to process audio with Aliyun ASR and (Mock) LLM
    """
    logger.info(f"Background task started for recording_id: {recording_id}")
    async with db_session_maker() as db:
        try:
            result = await db.execute(select(Recording).filter(Recording.id == recording_id))
            recording = result.scalars().first()
            if not recording:
                logger.error(f"Recording {recording_id} not found in background task")
                return

            # 1. Get Audio URL
            # Note: For Aliyun to work, this URL must be publicly accessible.
            # If running locally, you might need ngrok or use Mock mode (handled by service if keys missing)
            logger.info(f"Generating presigned URL for recording {recording_id} (key: {recording.s3_key})")
            file_url = storage_service.generate_presigned_url(recording.s3_key)
            logger.info(f"Generated URL for ASR: {file_url}")

            # If URL is local, warn user
            if "localhost" in file_url or "127.0.0.1" in file_url:
                logger.warning(f"Local URL detected: {file_url}. Aliyun ASR requires public URL.")
                # If we have keys, this will likely fail.
                # If we don't have keys, the service falls back to Mock, so it's fine.

            # 2. Call ASR
            logger.info(f"Updating status to processing and calling ASR for recording {recording_id}")
            recording.asr_status = "processing"
            await db.commit()

            transcription_result = await aliyun_asr_service.transcribe_audio(file_url)
            
            transcription = transcription_result.get("text", "")
            sentences = transcription_result.get("sentences", [])
            
            logger.info(
                f"ASR returned for recording {recording_id}. Transcription length: {len(transcription) if transcription else 0}"
            )

            if transcription and transcription_result.get("status") == "SUCCESS":
                recording.transcription_text = transcription
                if sentences:
                    recording.transcription_json = json.dumps(sentences, ensure_ascii=False)
                
                recording.asr_status = "completed"

                # 3. Call LLM Summary
                logger.info(f"Starting AI summary generation for recording {recording_id}")
                recording.summary_status = "processing"
                await db.commit()

                try:
                    # Fetch active LLM model
                    model_res = await db.execute(
                        select(LLMModel)
                        .filter(LLMModel.is_active == True)
                        .limit(1)
                    )
                    llm_model = model_res.scalars().first()

                    if llm_model:
                        try:
                            model = ModelFactory.create_model(llm_model)
                            agent = Agent(
                                model=model,
                                description="你是一个专业的会议纪要助手。",
                                instructions="请根据会议转写内容生成专业的会议纪要，并提取关键词。",
                                markdown=True
                            )

                            prompt = f"""
                            请根据以下会议转写内容，生成一份专业的会议纪要。

                            转写内容：
                            {transcription}

                            要求：
                            1. **会议主题**：简短的标题。
                            2. **主要讨论点**：使用项目符号列出。
                            3. **待办事项 (Action Items)**：列出任务和负责人（如果有）。
                            4. **关键词**：提取 5-10 个关键词。

                            请以 Markdown 格式输出。
                            在最后一行，请严格按照以下格式输出关键词（用于系统自动提取）：
                            __KEYWORDS__: keyword1, keyword2, keyword3
                            """

                            # Run in thread to avoid blocking
                            response = await asyncio.to_thread(agent.run, prompt)
                            full_content = response.content

                            # Parse Keywords
                            if "__KEYWORDS__:" in full_content:
                                parts = full_content.split("__KEYWORDS__:")
                                recording.summary_text = parts[0].strip()
                                recording.keywords = parts[1].strip()
                            else:
                                recording.summary_text = full_content
                                recording.keywords = ""
                            
                            recording.summary_status = "completed"
                        except Exception as inner_e:
                            logger.error(f"Agent execution failed: {inner_e}")
                            recording.summary_text = f"摘要生成失败: {str(inner_e)}"
                            recording.summary_status = "failed"
                    else:
                        recording.summary_text = "未找到激活的大模型，无法生成摘要。"
                        recording.summary_status = "failed"

                except Exception as e:
                    logger.error(f"Summary generation error: {e}")
                    recording.summary_text = f"处理出错: {str(e)}"
                    recording.summary_status = "failed"
                
                logger.info(f"Summary generation completed for recording {recording_id}")

                # 4. Recommendation (Real RAG)
                logger.info(f"Starting recommendation generation for recording {recording_id}")
                recording.recommendation_status = "processing"
                await db.commit()

                try:
                    # Use summary as query if available, otherwise transcription
                    query_text = ""
                    if recording.summary_text and len(recording.summary_text) > 10:
                        query_text = recording.summary_text
                    elif recording.transcription_text:
                        query_text = recording.transcription_text

                    # Truncate query for efficiency and better retrieval
                    if len(query_text) > 200:
                        query_text = query_text[:200]
                    
                    if not query_text:
                         query_text = recording.filename or "未知文档"

                    logger.info(f"Using query for recommendation: {query_text}")

                    # Search chunks
                    # Note: lightrag_engine is synchronous in search_chunks, but we can run it directly 
                    # as it mainly does vector search which is fast, or wrap in asyncio.to_thread if needed.
                    # Given it loads JSON cache, to_thread is safer.
                    results = await asyncio.to_thread(lightrag_engine.search_chunks, query=query_text, top_k=5)
                    
                    # Format results to JSON
                    recommendation_data = []
                    for item in results:
                         recommendation_data.append({
                             "id": item.get("doc_id"),
                             "title": item.get("title", "未知文档"),
                             "preview": item.get("preview", ""),
                             "score": item.get("score", 0),
                             "file_path": item.get("file_path", "")
                         })
                    
                    recording.recommendation_text = json.dumps(recommendation_data, ensure_ascii=False)
                    recording.recommendation_status = "completed"
                    logger.info(f"Recommendation generation completed. Found {len(recommendation_data)} items.")

                except Exception as e:
                    logger.error(f"Recommendation generation failed: {e}")
                    recording.recommendation_text = "[]" # Empty JSON array on failure
                    recording.recommendation_status = "failed"
            else:
                logger.warning(f"ASR failed (empty transcription) for recording {recording_id}")
                recording.transcription_text = "转写失败"
                recording.summary_text = "转写失败，无法生成摘要"
                recording.recommendation_text = "无法生成推荐"
                recording.asr_status = "failed"
                recording.summary_status = "failed"
                recording.recommendation_status = "failed"

            await db.commit()
            logger.info(f"Background task finished successfully for recording {recording_id}")

        except Exception as e:
            logger.error(f"Error processing recording {recording_id}: {e}", exc_info=True)
            recording.asr_status = "failed"
            recording.summary_status = "failed"
            recording.recommendation_status = "failed"
            await db.commit()


@router.post("/folder")
async def create_folder(name: str, parent_id: int = None, db: AsyncSession = Depends(get_db)):
    new_folder = Recording(
        filename=name,
        is_folder=True,
        parent_id=parent_id,
        format="folder",
        s3_key=None,  # Folders don't have S3 content
        transcription_text="",
        summary_text="",
    )
    db.add(new_folder)
    await db.commit()
    await db.refresh(new_folder)
    return new_folder


@router.put("/{recording_id}/rename")
async def rename_recording(recording_id: int, name: str, db: AsyncSession = Depends(get_db)):
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
    target_parent_id: int = None,  # None means root
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Recording).filter(Recording.id == recording_id))
    recording = result.scalars().first()
    if not recording:
        raise HTTPException(status_code=404, detail="Item not found")

    # Check if target folder exists (if not root)
    if target_parent_id is not None:
        target_result = await db.execute(
            select(Recording).filter(Recording.id == target_parent_id, Recording.is_folder == True)
        )
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
    parent_id: int = Form(None),  # Support upload to folder
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"Received upload request: filename={file.filename}, size={file.size}")

    # Generate unique key
    file_ext = os.path.splitext(file.filename)[1].lower()
    if not file_ext:
        file_ext = ".mp3"
    s3_key = f"{uuid.uuid4()}{file_ext}"

    # Process Audio (Resample to 16kHz for ASR) and Upload
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_orig:
        shutil.copyfileobj(file.file, tmp_orig)
        tmp_orig_path = tmp_orig.name

    converted_path = None
    success = False

    try:
        logger.info(f"Processing audio file: {tmp_orig_path}")

        # Use subprocess to call ffmpeg directly, bypassing pydub's ffprobe dependency
        import subprocess
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        
        # Determine output format (mp4 container for m4a/aac)
        export_format = file_ext.replace(".", "")
        if export_format == "m4a":
             export_format = "mp4"

        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{export_format}") as tmp_converted:
            converted_path = tmp_converted.name

        # Command: ffmpeg -y -i input -ar 16000 -ac 1 -f format output
        cmd = [
            ffmpeg_exe,
            "-y",
            "-i", tmp_orig_path,
            "-ar", "16000",
            "-ac", "1",
            "-f", export_format,
            converted_path
        ]
        
        logger.info(f"Running ffmpeg command: {' '.join(cmd)}")
        # Capture output for debugging
        process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if process.returncode != 0:
            logger.error(f"FFmpeg failed with return code {process.returncode}")
            logger.error(f"FFmpeg stderr: {process.stderr.decode('utf-8', errors='ignore')}")
            raise Exception("FFmpeg conversion failed")

        logger.info(f"Audio converted to 16kHz mono: {converted_path}")

        # Upload converted file
        with open(converted_path, "rb") as f_converted:
            logger.info(f"Uploading converted file to S3/OSS with key: {s3_key}")
            success = await storage_service.upload_file(f_converted, s3_key)

    except Exception as e:
        logger.error(f"Audio processing failed: {e}. Falling back to original file.")
        # Fallback to original
        file.file.seek(0)
        logger.info(f"Uploading original file to S3/OSS with key: {s3_key}")
        success = await storage_service.upload_file(file.file, s3_key)

    finally:
        # Cleanup temp files
        if os.path.exists(tmp_orig_path):
            os.unlink(tmp_orig_path)
        if converted_path and os.path.exists(converted_path):
            os.unlink(converted_path)

    if not success:
        logger.error("Upload failed")
        raise HTTPException(status_code=500, detail="Failed to upload file to S3")

    logger.info("Upload successful. Creating DB record...")

    # Save metadata to DB
    new_recording = Recording(
        filename=file.filename,
        s3_key=s3_key,
        format=file_ext.replace(".", ""),
        duration=duration,
        file_size=file.size if file.size else 0,
        parent_id=parent_id,
        is_folder=False,
        upload_status="completed",  # Upload is done at this point
        asr_status="pending",
        summary_status="pending",
        recommendation_status="pending",
        transcription_text="处理中...",
        transcription_json=None,
        summary_text="处理中...",
        recommendation_text="处理中...",
    )
    db.add(new_recording)
    await db.commit()
    await db.refresh(new_recording)

    logger.info(f"DB record created (ID: {new_recording.id}). Adding background task...")

    # Trigger Background Task for ASR
    background_tasks.add_task(process_audio_background, new_recording.id, AsyncSessionLocal)

    return new_recording


@router.get("/")
async def list_recordings(parent_id: int = None, skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    query = (
        select(Recording)
        .filter(Recording.parent_id == parent_id)
        .order_by(Recording.is_folder.desc(), Recording.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
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
    url = storage_service.generate_presigned_url(recording.s3_key)
    return {**recording.__dict__, "play_url": url}


@router.post("/{recording_id}/retry")
async def retry_transcription(recording_id: int, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
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
