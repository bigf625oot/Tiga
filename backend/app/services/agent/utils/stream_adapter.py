from __future__ import annotations

import logging
import re
import json
from typing import Any, AsyncGenerator, Dict, Optional
from enum import Enum, auto
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# =============================================================================
# Domain Entities 
# =============================================================================
@dataclass(slots=True)
class StreamEvent:
    """
    统一的 SSE 事件载体
    """
    type: str
    content: Any = ""
    sub_type: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """为下游 ControlPlane 提供的快速序列化入口"""
        result = {"type": self.type}
        if self.content:
            result["content"] = self.content
        if self.sub_type:
            result["sub_type"] = self.sub_type
        if self.data is not None:
            result["data"] = self.data
        return result


class StreamState(Enum):
    """显式状态机定义，消除布尔标志位组合爆炸 (Primitive Obsession)"""
    NORMAL = auto()
    THINKING = auto()
    IN_BLOCK = auto()

class AgnoStreamAdapter:
    """
    统一的流式内容转换器
    - 状态机驱动 (State Machine Driven): 消除冗长的 if-else 和字符串硬切片。
    - 强类型契约 (Strong Typed Contract): 返回 StreamEvent 领域实体。
    """
    def __init__(self, extract_charts: bool = True):
        self.extract_charts = extract_charts
        self._state = StreamState.NORMAL
        self._buffer = ""
        self._block_type: Optional[str] = None
        
        # 预编译正则，提升匹配性能
        self.BLOCK_START_PATTERN = re.compile(r":::\s*(\w+)")
        self.BLOCK_END_TAG = ":::"

    async def _flush_buffer(self) -> AsyncGenerator[StreamEvent, None]:
        """流结束时的收尾操作"""
        if not self._buffer:
            return

        if self._state == StreamState.IN_BLOCK:
            yield self._handle_block(self._block_type, self._buffer)
        elif self._state == StreamState.THINKING:
            yield StreamEvent(type="think", content=self._buffer)
        else:
            yield StreamEvent(type="content", content=self._buffer)
            
        self._buffer = ""
        self._state = StreamState.NORMAL

    def _handle_block(self, btype: Optional[str], raw_content: str) -> StreamEvent:
        """处理提取出来的块内容"""
        btype = btype or "unknown"
        if btype == "echarts" and self.extract_charts:
            try:
                data = json.loads(raw_content)
                return StreamEvent(type="chart", content=data, sub_type="echarts")
            except json.JSONDecodeError as e:
                logger.warning(f"Echarts JSON parse failed: {e}")
                return StreamEvent(type="content", content=f"\n```json\n{raw_content}\n```\n")
        
        return StreamEvent(type="content", content=f"\n```{btype}\n{raw_content}\n```\n")

    def _safe_to_dict(self, obj: Any) -> Dict[str, Any]:
        if hasattr(obj, "to_dict") and callable(obj.to_dict):
            return obj.to_dict()
        return {}

    async def to_standard_events(self, chunk: Any) -> AsyncGenerator[StreamEvent, None]:
        try:
            # 1. 拦截底层引擎的特殊结构
            if type(chunk).__name__ == "RunOutput":
                yield StreamEvent(type="run_output", data=self._safe_to_dict(chunk))
                return

            if hasattr(chunk, "tool_calls") and chunk.tool_calls:
                names = [tc.function.name for tc in chunk.tool_calls if getattr(tc, "function", None)]
                if names:
                    yield StreamEvent(type="status", content=f"Running tools: {', '.join(names)}...")

            # 2. 字典型事件映射 (字典流)
            if isinstance(chunk, dict) and "type" in chunk:
                t = chunk.get("type")
                
                # 在处理非内容事件前，清空文本缓冲区，确保时序正确
                if t not in ("content", "message", "final"):
                    async for out in self._flush_buffer():
                        yield out

                if t in ("reasoning", "thought", "thinking", "think"):
                    yield StreamEvent(type="think", content=chunk.get("content", ""))
                    return

                if t in ("tool_start", "tool_call", "tool_use", "call"):
                    data = chunk.get("content") if isinstance(chunk.get("content"), dict) else chunk
                    yield StreamEvent(
                        type="call",
                        content={
                            "tool": data.get("tool") or data.get("name") or "worker",
                            "args": data.get("args") or data.get("arguments") or {}
                        }
                    )
                    return

                if t in ("tool_result", "tool_end", "result"):
                    data = chunk.get("content") if isinstance(chunk.get("content"), dict) else chunk
                    yield StreamEvent(
                        type="result",
                        content={
                            "tool": data.get("tool") or data.get("name"),
                            "output": data.get("result") or data.get("output")
                        }
                    )
                    return

                if t == "content":
                    content_val = chunk.get("content", "")
                    if isinstance(content_val, str):
                        async for out in self._process_content(content_val):
                            yield out
                    else:
                        yield StreamEvent(type="content", content=str(content_val))
                    return
                
                if t in ("message", "final"):
                    msg = chunk.get("message") or chunk.get("final_message")
                    content_val = getattr(msg, "content", None) or str(msg)
                    async for out in self._process_content(content_val):
                        yield out
                    return

                yield StreamEvent(type="unknown", content=chunk)
                return

            # 3. 纯文本事件
            if isinstance(chunk, str):
                async for out in self._process_content(chunk):
                    yield out
                return

            # 4. Agno/Pydantic 对象事件
            event_type = getattr(chunk, "event", None)
            if isinstance(event_type, str):
                # 拦截底层的工具调用事件，避免将其转换为文本输出污染对话流
                if event_type == "ToolCallStarted":
                    tools = getattr(chunk, "tools", [])
                    if tools and isinstance(tools, list):
                        for tool in tools:
                            yield StreamEvent(
                                type="call",
                                content={
                                    "tool": getattr(tool, "tool_name", "worker"),
                                    "args": getattr(tool, "tool_args", {})
                                }
                            )
                    return
                elif event_type in ("ToolCallCompleted", "ToolCallError"):
                    tools = getattr(chunk, "tools", [])
                    if tools and isinstance(tools, list):
                        for tool in tools:
                            error_msg = getattr(tool, "tool_call_error", None)
                            yield StreamEvent(
                                type="result",
                                content={
                                    "tool": getattr(tool, "tool_name", "worker"),
                                    "output": getattr(tool, "result", ""),
                                    "is_error": bool(error_msg) or event_type == "ToolCallError",
                                    "logs": [error_msg] if error_msg else []
                                }
                            )
                    return
                elif event_type in ("RunStarted", "RunCompleted", "ModelRequestStarted", "ModelRequestCompleted", "RunContentCompleted", "RunIntermediateContent"):
                    # Safe to ignore these purely internal lifecycle events to prevent noise and duplicates
                    return

            reasoning = getattr(chunk, "thinking", None) or getattr(chunk, "reasoning", None)
            if isinstance(reasoning, str) and reasoning:
                yield StreamEvent(type="think", content=reasoning)

            content = getattr(chunk, "content", None)
            if isinstance(content, str) and content:
                async for out in self._process_content(content):
                    yield out
                return

            if content is not None:
                yield StreamEvent(type="content", content=str(content))

        except Exception as e:
            logger.error(f"Stream adapt failed: {e}", exc_info=True)
            yield StreamEvent(type="error", content="Stream processing error")

    async def flush(self) -> AsyncGenerator[StreamEvent, None]:
        async for out in self._flush_buffer():
            yield out

    async def _process_content(self, content: str) -> AsyncGenerator[StreamEvent, None]:
        """
        状态机解析器 (State Machine Parser)
        """
        if not content:
            return

        self._buffer += content

        while True:
            if self._state == StreamState.NORMAL:
                match = self.BLOCK_START_PATTERN.search(self._buffer)
                if match:
                    pre_text = self._buffer[:match.start()]
                    if pre_text:
                        yield StreamEvent(type="content", content=pre_text)
                    self._state = StreamState.IN_BLOCK
                    self._block_type = match.group(1)
                    self._buffer = self._buffer[match.end():]
                    continue

                think_idx = self._buffer.find("<think>")
                if think_idx != -1:
                    if think_idx > 0:
                        yield StreamEvent(type="content", content=self._buffer[:think_idx])
                    self._state = StreamState.THINKING
                    self._buffer = self._buffer[think_idx + 7:]
                    continue

                last_lt = self._buffer.rfind("<")
                if last_lt != -1:
                    potential = self._buffer[last_lt:]
                    if "<think>".startswith(potential):
                        if last_lt > 0:
                            yield StreamEvent(type="content", content=self._buffer[:last_lt])
                        self._buffer = potential
                        break

                safe_len = max(0, len(self._buffer) - 10)
                if safe_len > 0:
                    yield StreamEvent(type="content", content=self._buffer[:safe_len])
                    self._buffer = self._buffer[safe_len:]
                break

            elif self._state == StreamState.IN_BLOCK:
                end_idx = self._buffer.find(self.BLOCK_END_TAG)
                if end_idx != -1:
                    raw_block = self._buffer[:end_idx].strip()
                    yield self._handle_block(self._block_type, raw_block)
                    self._state = StreamState.NORMAL
                    self._block_type = None
                    self._buffer = self._buffer[end_idx + len(self.BLOCK_END_TAG):]
                    continue
                break

            elif self._state == StreamState.THINKING:
                end_idx = self._buffer.find("</think>")
                if end_idx != -1:
                    if end_idx > 0:
                        yield StreamEvent(type="think", content=self._buffer[:end_idx])
                    self._state = StreamState.NORMAL
                    self._buffer = self._buffer[end_idx + 8:]
                    continue

                last_lt = self._buffer.rfind("<")
                if last_lt != -1:
                    potential = self._buffer[last_lt:]
                    if "</think>".startswith(potential):
                        if last_lt > 0:
                            yield StreamEvent(type="think", content=self._buffer[:last_lt])
                        self._buffer = potential
                        break

                if self._buffer:
                    yield StreamEvent(type="think", content=self._buffer)
                    self._buffer = ""
                break

