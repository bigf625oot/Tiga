import asyncio
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from app.services.rag.knowledge.parser import parse_document
from app.services.rag.knowledge.parsing.backends import ParseChunk
from app.services.rag.knowledge.parsing.orchestrator import parse_bytes_chunks


class _FailBackend:
    name = "fail"

    def parse_path(self, file_path: str):
        raise ImportError("missing")

    def parse_bytes(self, content: bytes, filename: str, content_type: str | None):
        raise ImportError("missing")


class _BadTextBackend:
    name = "bad"

    def parse_path(self, file_path: str):
        return [ParseChunk(page=1, text="\ue000" * 100, meta={"backend": self.name})]

    def parse_bytes(self, content: bytes, filename: str, content_type: str | None):
        return [ParseChunk(page=1, text="\ue000" * 100, meta={"backend": self.name})]


class _OkBackend:
    name = "ok"

    def __init__(self, text: str):
        self._text = text

    def parse_path(self, file_path: str):
        return [ParseChunk(page=1, text=self._text, meta={"backend": self.name})]

    def parse_bytes(self, content: bytes, filename: str, content_type: str | None):
        return [ParseChunk(page=1, text=self._text, meta={"backend": self.name})]


class _DummyUploadFile:
    def __init__(self, content: bytes, filename: str, content_type: str):
        self._content = content
        self.filename = filename
        self.content_type = content_type

    async def read(self) -> bytes:
        return self._content


class TestRagParserOrchestrator(unittest.TestCase):
    def test_pdf_backend_fallback_on_import_error(self):
        chunks = parse_bytes_chunks(
            b"%PDF-1.4",
            "a.pdf",
            "application/pdf",
            pdf_backends=[_FailBackend(), _OkBackend("hello")],
        )
        self.assertEqual(chunks[0]["text"], "hello")

    def test_pdf_backend_fallback_on_bad_text(self):
        chunks = parse_bytes_chunks(
            b"%PDF-1.4",
            "a.pdf",
            "application/pdf",
            pdf_backends=[_BadTextBackend(), _OkBackend("valid text")],
        )
        self.assertEqual(chunks[0]["text"], "valid text")

    def test_parse_document_uses_markdown_title(self):
        dummy = _DummyUploadFile(b"ignored", "test.pdf", "application/pdf")
        with patch("app.services.rag.knowledge.parser.parse_bytes_chunks") as m:
            m.return_value = [{"page": 1, "text": "abc"}]
            out = asyncio.run(parse_document(dummy))
        self.assertTrue(out.startswith("# test"))
        self.assertIn("abc", out)

    def test_parse_document_text_decode_error(self):
        dummy = _DummyUploadFile(b"\xff", "a.txt", "text/plain")
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(parse_document(dummy))
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("无法解码文件内容", ctx.exception.detail)


if __name__ == "__main__":
    unittest.main()

