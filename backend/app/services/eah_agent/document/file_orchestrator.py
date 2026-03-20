import asyncio
import io
import logging
from pathlib import Path
from typing import Any, Union, Dict, List

from app.services.eah_agent.document.file_processors import FileProcessorFactory

logger = logging.getLogger(__name__)

class FileOrchestrator:
    """
    统一门面：Agent 直接调用的入口
    处理单个文件及批量文件
    """
    @staticmethod
    async def process_file(
        file_source: Union[str, bytes, Path, io.BytesIO, Any],
        filename: str,
        session_id: str = None,
        kb_manager: Any = None,
        **kwargs: Any,
    ):
        file_bytes = await FileOrchestrator._read_bytes(file_source)
        processor = FileProcessorFactory.get_processor(filename)
        return await processor.process(file_bytes, filename, kb_manager=kb_manager)

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
    async def process_batch(files: Any, session_id: str, kb_manager: Any = None, **kwargs: Any):
        if not files:
            return {"context": "", "media": [], "results": []}

        async def _one(f: Any):
            file_obj = getattr(f, "file", f)
            filename = getattr(f, "filename", "unknown_file")
            return await FileOrchestrator.process_file(file_obj, filename, session_id=session_id, kb_manager=kb_manager)

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
