from __future__ import annotations

import logging
from typing import Any, AsyncGenerator, Dict

logger = logging.getLogger(__name__)


class AgnoStreamAdapter:
    def __init__(self):
        self._is_thinking = False
        self._buffer = ""

    async def to_standard_events(self, chunk: Any) -> AsyncGenerator[Dict[str, Any], None]:
        try:
            if isinstance(chunk, dict) and "type" in chunk:
                yield chunk
                return

            if isinstance(chunk, str):
                async for out in self._process_content(chunk):
                    yield out
                return

            reasoning = getattr(chunk, "thinking", None) or getattr(chunk, "reasoning", None)
            if isinstance(reasoning, str) and reasoning:
                yield {"type": "think", "content": reasoning}

            content = getattr(chunk, "content", None)
            if isinstance(content, str) and content:
                async for out in self._process_content(content):
                    yield out
                return

            if content is not None:
                yield {"type": "content", "content": str(content)}
        except Exception as e:
            logger.error(f"Stream adapt failed: {e}", exc_info=True)
            yield {"type": "error", "content": "Stream processing error"}

    async def _process_content(self, content: str) -> AsyncGenerator[Dict[str, Any], None]:
        if not content:
            return

        self._buffer += content
        buffer = self._buffer

        while True:
            if not self._is_thinking:
                start_idx = buffer.find("<think>")
                if start_idx != -1:
                    if start_idx > 0:
                        yield {"type": "content", "content": buffer[:start_idx]}
                    self._is_thinking = True
                    buffer = buffer[start_idx + 7 :]
                    continue

                last_lt = buffer.rfind("<")
                if last_lt == -1:
                    if buffer:
                        yield {"type": "content", "content": buffer}
                    buffer = ""
                    break

                potential = buffer[last_lt:]
                if "<think>".startswith(potential):
                    if last_lt > 0:
                        yield {"type": "content", "content": buffer[:last_lt]}
                    buffer = potential
                    break

                if last_lt > 0:
                    yield {"type": "content", "content": buffer[:last_lt]}
                buffer = buffer[last_lt:]
                if not "<think>".startswith(buffer):
                    yield {"type": "content", "content": buffer}
                    buffer = ""
                break

            end_idx = buffer.find("</think>")
            if end_idx != -1:
                if end_idx > 0:
                    yield {"type": "think", "content": buffer[:end_idx]}
                self._is_thinking = False
                buffer = buffer[end_idx + 8 :]
                continue

            last_lt = buffer.rfind("<")
            if last_lt == -1:
                if buffer:
                    yield {"type": "think", "content": buffer}
                buffer = ""
                break

            potential = buffer[last_lt:]
            if "</think>".startswith(potential):
                if last_lt > 0:
                    yield {"type": "think", "content": buffer[:last_lt]}
                buffer = potential
                break

            if last_lt > 0:
                yield {"type": "think", "content": buffer[:last_lt]}
            buffer = buffer[last_lt:]
            if not "</think>".startswith(buffer):
                yield {"type": "think", "content": buffer}
                buffer = ""
            break

        self._buffer = buffer

