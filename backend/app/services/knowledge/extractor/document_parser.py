"""
文档解析器
功能：
- 解析本地文件（PDF、DOCX）
- 提取文本内容
- 支持分页处理
"""
import io
import logging
import os
from typing import List, Dict, Any
from fastapi import HTTPException, UploadFile
from app.services.utils.markdown import to_markdown
from app.services.knowledge.extractor.parsers.orchestrator import parse_bytes_chunks, parse_path_chunks
from app.services.knowledge.extractor.parsers.text import sanitize_text

logger = logging.getLogger(__name__)


def parse_local_file(file_path: str) -> str:
    """
    Parse a local file and return text content.
    Wrapper around parse_local_file_chunks for backward compatibility.
    """
    chunks = parse_local_file_chunks(file_path)
    full_text = "\n".join([c.get("text", "") for c in chunks])
    
    # Add markdown formatting if needed (compatibility)
    full_text = to_markdown(full_text, {"source": "local", "title": os.path.splitext(os.path.basename(file_path))[0]})
    return full_text

def parse_local_file_chunks(file_path: str) -> List[Dict[str, Any]]:
    """
    Parse a local file and return a list of page/chunk dictionaries.
    Returns: [{"page": 1, "text": "..."}, ...]
    """
    try:
        return parse_path_chunks(file_path)
    except Exception as e:
        logger.error(f"Error parsing local file {file_path}: {e}")
        return []


async def parse_document(file: UploadFile) -> str:
    """
    Parse uploaded document (PDF or Word) and return text content.
    """
    content_type = file.content_type
    filename = file.filename.lower()

    try:
        content = await file.read()
        io.BytesIO(content)

        text = ""

        if filename.endswith(".pdf") or content_type == "application/pdf":
            chunks = parse_bytes_chunks(content, file.filename, content_type)
            text = "\n".join([c.get("text", "") for c in chunks]).strip()
            if not text:
                raise HTTPException(
                    status_code=400,
                    detail="未提取到文本内容。如果是扫描版 PDF，请先使用 OCR 工具或开启 OCR_ENABLED。",
                )

        elif filename.endswith((".docx", ".doc")) or (content_type and "word" in content_type):
            # python-docx only supports .docx
            if filename.endswith(".doc"):
                raise HTTPException(status_code=400, detail="暂不支持旧版 .doc 格式，请另存为 .docx 后上传")
            chunks = parse_bytes_chunks(content, file.filename, content_type)
            text = "\n".join([c.get("text", "") for c in chunks]).strip()
            if not text:
                raise HTTPException(status_code=400, detail="未提取到文本内容。文档可能只包含图片或表格。")
        else:
            chunks = parse_bytes_chunks(content, file.filename, content_type)
            text = "\n".join([c.get("text", "") for c in chunks]).strip()
            if not text:
                raise HTTPException(status_code=400, detail="未提取到文本内容。")

        text = sanitize_text(text.strip())
        text = to_markdown(text, {"source": "upload", "title": os.path.splitext(file.filename)[0]})
        return text

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Error parsing document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to parse document: {str(e)}")
