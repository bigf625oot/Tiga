from __future__ import annotations

import logging
import re
import json
from typing import Any, AsyncGenerator, Dict, Optional

logger = logging.getLogger(__name__)


class AgnoStreamAdapter:
    """
    统一的流式内容转换器 (P10 级实现)
    整合了：1. Think 标签断裂解析 2. 工具调用映射 3. 错误捕获 4. ::: echarts 图表块提取
    统一输出规范：
      - {"type": "think", "content": "..."}
      - {"type": "content", "content": "..."}
      - {"type": "call", "content": {"tool": "...", "args": {...}}}
      - {"type": "result", "content": {"tool": "...", "output": "..."}}
      - {"type": "chart", "content": {...}, "sub_type": "echarts"}
      - {"type": "run_output", "data": {...}}
      - {"type": "status", "content": "..."}
      - {"type": "error", "content": "..."}
    """
    def __init__(self, extract_charts: bool = True):
        self.extract_charts = extract_charts
        self._is_thinking = False
        self._buffer = ""
        # 块提取状态 (data_handler 迁移)
        self._in_block = False
        self._block_type: Optional[str] = None
        self.BLOCK_START_PATTERN = re.compile(r":::\s*(\w+)")
        self.BLOCK_END_TAG = ":::"

    async def _flush_buffer(self) -> AsyncGenerator[Dict[str, Any], None]:
        """将缓冲区中剩余的内容输出"""
        if self._buffer:
            if self._in_block:
                yield self._handle_block(self._block_type, self._buffer)
            elif self._is_thinking:
                yield {"type": "think", "content": self._buffer}
            else:
                yield {"type": "content", "content": self._buffer}
            self._buffer = ""
            self._in_block = False
            self._is_thinking = False

    def _handle_block(self, btype: str, raw_content: str) -> Dict[str, Any]:
        """处理提取出来的块内容 (data_handler 迁移)"""
        if btype == "echarts" and self.extract_charts:
            try:
                data = json.loads(raw_content)
                return {"type": "chart", "content": data, "sub_type": "echarts"}
            except Exception as e:
                logger.warning(f"Echarts JSON parse failed: {e}")
                return {"type": "content", "content": f"\n```json\n{raw_content}\n```\n"}
        
        # 默认作为代码块回退
        return {"type": "content", "content": f"\n```{btype}\n{raw_content}\n```\n"}

    def _safe_to_dict(self, obj: Any) -> Dict[str, Any]:
        try:
            return obj.to_dict() if hasattr(obj, "to_dict") else str(obj)
        except:
            return {}

    async def to_standard_events(self, chunk: Any) -> AsyncGenerator[Dict[str, Any], None]:
        try:
            # 0. 处理 RunOutput 元数据 (data_handler 迁移)
            if type(chunk).__name__ == "RunOutput":
                yield {"type": "run_output", "data": self._safe_to_dict(chunk)}
                return

            # 处理工具调用状态 (data_handler 迁移)
            if hasattr(chunk, "tool_calls") and chunk.tool_calls:
                names = [tc.function.name for tc in chunk.tool_calls if hasattr(tc, "function") and tc.function]
                if names:
                    yield {"type": "status", "content": f"Running tools: {', '.join(names)}..."}
            # 1. 处理结构化字典 (兼容之前的 normalizer 逻辑)
            if isinstance(chunk, dict) and "type" in chunk:
                t = chunk.get("type")
                
                # 在处理非纯文本类型的事件前，先把缓冲区里的残留文本吐出
                if t not in ("content", "message", "final"):
                    async for out in self._flush_buffer():
                        yield out

                if t in ("reasoning", "thought", "thinking", "think"):
                    yield {"type": "think", "content": chunk.get("content", "")}
                    return

                elif t in ("tool_start", "tool_call", "tool_use", "call"):
                    data = chunk.get("content") if isinstance(chunk.get("content"), dict) else chunk
                    yield {
                        "type": "call",
                        "content": {
                            "tool": data.get("tool") or data.get("name") or "worker",
                            "args": data.get("args") or data.get("arguments") or {}
                        }
                    }
                    return

                elif t in ("tool_result", "tool_end", "result"):
                    data = chunk.get("content") if isinstance(chunk.get("content"), dict) else chunk
                    yield {
                        "type": "result",
                        "content": {
                            "tool": data.get("tool") or data.get("name"),
                            "output": data.get("result") or data.get("output")
                        }
                    }
                    return

                elif t == "content":
                    content_val = chunk.get("content", "")
                    if isinstance(content_val, str):
                        async for out in self._process_content(content_val):
                            yield out
                    else:
                        yield {"type": "content", "content": str(content_val)}
                    return
                
                elif t in ("message", "final"):
                    msg = chunk.get("message") or chunk.get("final_message")
                    content_val = getattr(msg, "content", None) or str(msg)
                    async for out in self._process_content(content_val):
                        yield out
                    return

                # 未知或透传类型
                yield chunk
                return

            # 2. 处理纯文本
            if isinstance(chunk, str):
                async for out in self._process_content(chunk):
                    yield out
                return

            # 3. 处理 Agno / Pydantic 对象
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

    async def flush(self) -> AsyncGenerator[Dict[str, Any], None]:
        """流结束时调用，清空残留 buffer"""
        async for out in self._flush_buffer():
            yield out

    async def _process_content(self, content: str) -> AsyncGenerator[Dict[str, Any], None]:
        if not content:
            return

        self._buffer += content
        buffer = self._buffer

        while True:
            # ----- 1. 图表块解析逻辑 -----
            if not self._in_block and not self._is_thinking:
                match = self.BLOCK_START_PATTERN.search(buffer)
                if match:
                    pre_text = buffer[:match.start()]
                    if pre_text:
                        yield {"type": "content", "content": pre_text}
                    self._in_block = True
                    self._block_type = match.group(1)
                    buffer = buffer[match.end():]
                    continue

            if self._in_block:
                end_idx = buffer.find(self.BLOCK_END_TAG)
                if end_idx != -1:
                    raw_block = buffer[:end_idx].strip()
                    yield self._handle_block(self._block_type, raw_block)
                    self._in_block = False
                    self._block_type = None
                    buffer = buffer[end_idx + len(self.BLOCK_END_TAG):]
                    continue
                else:
                    break

            # ----- 2. <think> 标签解析逻辑 -----
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
                    # 为了给 ::: 留出安全缓冲区 (避免截断)
                    safe_len = max(0, len(buffer) - 10)
                    if safe_len > 0:
                        yield {"type": "content", "content": buffer[:safe_len]}
                        buffer = buffer[safe_len:]
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

