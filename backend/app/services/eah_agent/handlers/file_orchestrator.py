import asyncio
import io
import logging
from pathlib import Path
from typing import Any, Union, Dict, List

from agno.media import Image

logger = logging.getLogger(__name__)


class FileOrchestrator:
    @staticmethod
    async def process_file(
        file_source: Union[str, bytes, Path, io.BytesIO, Any],
        filename: str,
        session_id: str = None,
        **kwargs: Any,
    ):
        file_bytes = await FileOrchestrator._read_bytes(file_source)
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        if ext in {"jpg", "jpeg", "png", "gif", "webp"}:
            try:
                image_obj = Image(content=file_bytes, filepath=filename)
                return {
                    "status": "success",
                    "file_type": "image",
                    "filename": filename,
                    "content_text": f"[图片文件: {filename}]",
                    "media_objects": [image_obj],
                    "metadata": {},
                    "error_msg": None,
                }
            except Exception as e:
                return {
                    "status": "error",
                    "file_type": "image",
                    "filename": filename,
                    "content_text": None,
                    "media_objects": [],
                    "metadata": {},
                    "error_msg": str(e),
                }

        if ext == "pdf":
            try:
                from pypdf import PdfReader
            except Exception:
                PdfReader = None

            if not PdfReader:
                return {
                    "status": "error",
                    "file_type": "pdf",
                    "filename": filename,
                    "content_text": None,
                    "media_objects": [],
                    "metadata": {},
                    "error_msg": "pypdf not installed",
                }

            try:
                reader = PdfReader(io.BytesIO(file_bytes))
                text_parts: List[str] = []
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text_parts.append(extracted)
                final_text = "\n".join(text_parts)
                if len(final_text.strip()) < 10 and len(reader.pages) > 0:
                    final_text = f"[警告: {filename} 可能是扫描件，无法提取文本，请使用多模态模型查看图片]"
                return {
                    "status": "success",
                    "file_type": "pdf",
                    "filename": filename,
                    "content_text": final_text[:8000],
                    "media_objects": [],
                    "metadata": {"page_count": len(reader.pages)},
                    "error_msg": None,
                }
            except Exception as e:
                return {
                    "status": "error",
                    "file_type": "pdf",
                    "filename": filename,
                    "content_text": None,
                    "media_objects": [],
                    "metadata": {},
                    "error_msg": str(e),
                }

        try:
            text_content = file_bytes.decode("utf-8", errors="replace")
        except Exception:
            text_content = ""

        return {
            "status": "success",
            "file_type": "text",
            "filename": filename,
            "content_text": text_content[:8000] if text_content else None,
            "media_objects": [],
            "metadata": {"char_count": len(text_content)},
            "error_msg": None,
        }

    @staticmethod
    async def _read_bytes(file_source: Union[str, bytes, Path, io.BytesIO, Any]) -> bytes:
        if isinstance(file_source, bytes):
            return file_source
        if isinstance(file_source, io.BytesIO):
            return file_source.getvalue()
        if isinstance(file_source, (str, Path)):
            return Path(file_source).read_bytes()

        def _read(src: Any) -> bytes:
            data = src.read()
            try:
                src.seek(0)
            except Exception:
                pass
            if isinstance(data, bytes):
                return data
            try:
                return bytes(data)
            except Exception:
                return b""

        return await asyncio.to_thread(_read, file_source)

    @staticmethod
    async def process_batch(files: Any, session_id: str, **kwargs: Any):
        if not files:
            return {"context": "", "media": [], "results": []}

        async def _one(f: Any):
            file_obj = getattr(f, "file", f)
            filename = getattr(f, "filename", "unknown_file")
            return await FileOrchestrator.process_file(file_obj, filename, session_id=session_id)

        results = await asyncio.gather(*[_one(f) for f in files], return_exceptions=True)

        contexts = []
        media = []
        for r in results:
            if isinstance(r, Exception):
                logger.error(f"File processing failed: {r}")
                continue
            if not isinstance(r, dict):
                continue
            txt = r.get("content_text")
            if isinstance(txt, str) and txt:
                contexts.append(txt)
            objs = r.get("media_objects") or []
            if isinstance(objs, list) and objs:
                media.extend(objs)

        return {"context": "\n\n".join(contexts), "media": media, "results": results}
