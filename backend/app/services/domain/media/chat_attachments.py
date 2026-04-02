import asyncio
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
 
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
 
from app.models.knowledge import DocumentStatus, KnowledgeDocument
from app.services.domain.media.asr import aliyun_asr_service
from app.services.intelligence.knowledge.rag.retrieval.engines.lightrag import lightrag_engine
from app.services.platform.storage.service import storage_service
 
 
def normalize_doc_ids(raw: Optional[List[Any]]) -> List[int]:
    if not raw:
        return []
    out: List[int] = []
    for v in raw:
        if v is None:
            continue
        if isinstance(v, int):
            out.append(v)
            continue
        s = str(v).strip()
        if not s:
            continue
        if s.isdigit():
            out.append(int(s))
    dedup: List[int] = []
    seen = set()
    for x in out:
        if x not in seen:
            seen.add(x)
            dedup.append(x)
    return dedup
 
 
async def ingest_chat_file(db: AsyncSession, file: UploadFile) -> Dict[str, Any]:
    content = await file.read()
    filename = file.filename or "upload"
    content_type = (file.content_type or "").lower()
 
    oss_key = f"chat_uploads/{uuid.uuid4().hex}_{Path(filename).name}"
    oss_url = storage_service.upload_file_sync(oss_key, content)
 
    doc = KnowledgeDocument(
        filename=Path(filename).name,
        oss_key=oss_key,
        oss_url=oss_url,
        file_size=len(content),
        status=DocumentStatus.UPLOADED,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
 
    extracted_text = ""
    media_kind = "file"
    try:
        if content_type.startswith("image/"):
            media_kind = "image"
            extracted_text = await asyncio.to_thread(_extract_image_text, content)
        elif content_type.startswith("video/"):
            media_kind = "video"
            extracted_text = await _extract_media_asr_text(content, filename, oss_url, prefer_url=True)
        elif content_type.startswith("audio/"):
            media_kind = "audio"
            extracted_text = await _extract_media_asr_text(content, filename, oss_url, prefer_url=True)
        else:
            extracted_text = ""
    except Exception:
        extracted_text = ""
 
    extracted_text = (extracted_text or "").strip()
    if extracted_text:
        try:
            await lightrag_engine.insert_text_async(extracted_text, description=f"doc#{doc.id}:{doc.filename}")
            doc.status = DocumentStatus.INDEXED
            doc.error_message = None
        except Exception as e:
            doc.status = DocumentStatus.FAILED
            doc.error_message = str(e)
    else:
        doc.status = DocumentStatus.UPLOADED
        doc.error_message = "no_extractable_text"
 
    db.add(doc)
    await db.commit()
    return {
        "id": doc.id,
        "name": doc.filename,
        "title": doc.filename,
        "size": doc.file_size,
        "oss_url": doc.oss_url,
        "media_kind": media_kind,
        "status": doc.status.value,
        "error_message": doc.error_message,
        "extracted_text": extracted_text,
    }
 
 
def _extract_image_text(content: bytes) -> str:
    try:
        from PIL import Image
    except Exception:
        return ""
    try:
        import io
        img = Image.open(io.BytesIO(content))
        img.load()
    except Exception:
        return ""
    try:
        import pytesseract
    except Exception:
        return ""
    try:
        return pytesseract.image_to_string(img) or ""
    except Exception:
        return ""
 
 
async def _extract_media_asr_text(content: bytes, filename: str, file_url: str, prefer_url: bool) -> str:
    if prefer_url and file_url:
        try:
            r = await aliyun_asr_service.transcribe_audio(file_url)
            if r and r.get("status") == "SUCCESS" and (r.get("text") or "").strip():
                return str(r.get("text") or "")
        except Exception:
            pass
 
    suffix = Path(filename).suffix or ""
    tmp_dir = Path(os.getenv("TEMP") or os.getcwd()) / "tiga_chat_media"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    src_path = tmp_dir / f"{uuid.uuid4().hex}{suffix}"
    audio_path = tmp_dir / f"{uuid.uuid4().hex}.wav"
    try:
        src_path.write_bytes(content)
        try:
            import warnings
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=RuntimeWarning, module="pydub")
                from pydub import AudioSegment
            import imageio_ffmpeg
            AudioSegment.converter = imageio_ffmpeg.get_ffmpeg_exe()
            audio = AudioSegment.from_file(str(src_path))
            audio.export(str(audio_path), format="wav")
        except Exception:
            return ""
 
        audio_bytes = audio_path.read_bytes()
        audio_key = f"chat_uploads/{uuid.uuid4().hex}.wav"
        audio_url = storage_service.upload_file_sync(audio_key, audio_bytes)
        r2 = await aliyun_asr_service.transcribe_audio(audio_url)
        if r2 and r2.get("status") == "SUCCESS":
            return str(r2.get("text") or "")
        return ""
    finally:
        try:
            if src_path.exists():
                src_path.unlink()
        except Exception:
            pass
        try:
            if audio_path.exists():
                audio_path.unlink()
        except Exception:
            pass
