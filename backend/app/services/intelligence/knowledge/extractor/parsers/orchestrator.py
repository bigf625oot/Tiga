import os
from typing import Any, Dict, List, Optional, Sequence

from fastapi import HTTPException

from app.core.config import settings

from .backends import ParseBackend, ParseChunk, build_default_backends
from .text import is_text_valid


def _split_order(s: Optional[str], default: Sequence[str]) -> List[str]:
    if not s:
        return list(default)
    return [p.strip() for p in s.split(",") if p.strip()]


def _chunks_to_dicts(chunks: List[ParseChunk]) -> List[Dict[str, Any]]:
    return [c.to_dict() for c in chunks]


def _first_success(
    backends: Sequence[ParseBackend],
    parse_fn,
) -> List[ParseChunk]:
    last_error: Optional[Exception] = None
    for backend in backends:
        try:
            chunks = parse_fn(backend) or []
        except HTTPException:
            raise
        except ImportError as e:
            last_error = e
            continue
        except Exception as e:
            last_error = e
            continue
        if chunks:
            full_text = "\n".join([(c.text or "") for c in chunks]).strip()
            if not full_text:
                continue
            if not is_text_valid(full_text):
                continue
            return chunks
    if last_error:
        return []
    return []


def parse_path_chunks(
    file_path: str, pdf_backends: Optional[Sequence[ParseBackend]] = None
) -> List[Dict[str, Any]]:
    filename = os.path.basename(file_path).lower()

    if filename.endswith(".pdf"):
        order = _split_order(
            getattr(settings, "DOC_PARSE_PDF_BACKENDS", None),
            ["docling", "pymupdf", "pdfplumber", "pypdf", "ocr"],
        )
        backends = list(pdf_backends) if pdf_backends is not None else build_default_backends(order)
        chunks = _first_success(backends, lambda b: b.parse_path(file_path))
        return _chunks_to_dicts(chunks)

    if filename.endswith(".docx"):
        backends = build_default_backends(["docx"])
        chunks = _first_success(backends, lambda b: b.parse_path(file_path))
        return _chunks_to_dicts(chunks)

    backends = build_default_backends(["text"])
    chunks = _first_success(backends, lambda b: b.parse_path(file_path))
    return _chunks_to_dicts(chunks)


def parse_bytes_chunks(
    content: bytes,
    filename: str,
    content_type: Optional[str],
    pdf_backends: Optional[Sequence[ParseBackend]] = None,
) -> List[Dict[str, Any]]:
    lower_name = (filename or "").lower()

    if lower_name.endswith(".pdf") or content_type == "application/pdf":
        order = _split_order(
            getattr(settings, "DOC_PARSE_PDF_BACKENDS", None),
            ["docling", "pymupdf", "pdfplumber", "pypdf", "ocr"],
        )
        backends = list(pdf_backends) if pdf_backends is not None else build_default_backends(order)
        chunks = _first_success(backends, lambda b: b.parse_bytes(content, filename, content_type))
        return _chunks_to_dicts(chunks)

    if lower_name.endswith((".docx", ".doc")) or (content_type and "word" in content_type):
        backends = build_default_backends(["docx"])
        chunks = _first_success(backends, lambda b: b.parse_bytes(content, filename, content_type))
        return _chunks_to_dicts(chunks)

    backends = build_default_backends(["text"])
    chunks = _first_success(backends, lambda b: b.parse_bytes(content, filename, content_type))
    return _chunks_to_dicts(chunks)
