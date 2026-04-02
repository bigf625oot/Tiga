from __future__ import annotations

import logging
import re
import json
import time
from typing import Any, AsyncGenerator, Dict, Optional, Set
from enum import Enum, auto
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# =============================================================================
# 领域实体
# =============================================================================
class StreamEventType(str, Enum):
    """
    全生命周期事件类型字典，覆盖四大维度。
    """
    # --- 1. 内容流 (Content Stream) --- 
    TEXT_DELTA = "text_delta"           # 最终回复增量 
    THINK_DELTA = "think_delta"         # 思考链增量 (Reasoning/Thought) 
    
    # --- 2. 工具执行链 (Logic / Tool Execution Chain) --- 
    TOOL_CALL_CREATED = "tool_created"   # 模型决定使用工具（含参数推导中） 
    TOOL_CALL_START = "tool_start"       # 工具开始进入本地执行 
    TOOL_CALL_END = "tool_end"           # 工具执行成功返回 
    TOOL_CALL_ERROR = "tool_error"       # 工具执行抛出异常 
    
    # --- 3. 知识发现与块 (Knowledge & Blocks) --- 
    KNOWLEDGE_RETRIEVED = "knowledge"    # RAG 检索到的参考片段 
    CHART_BLOCK = "chart"                # 渲染 ECharts/AntV 等 
    MEDIA_BLOCK = "media"                # 视频、音频、图片 
    
    # --- 4. 运行生命周期 (Lifecycle) --- 
    RUN_STAGE_CHANGED = "stage_change"   # 阶段切换 (Planning -> Executing) 
    RUN_COMPLETED = "run_completed"      # 整个流程彻底结束 
    
    # --- 5. 计量与诊断 (Telemetry) --- 
    METRICS_UPDATE = "metrics"           # Token、耗时、模型元数据 
    DEBUG_LOG = "debug"                  # 内部状态调试
    
    # --- 系统状态 (System Status) ---
    STATUS_UPDATE = "status"             # 系统运行状态文本
    ERROR = "error"                      # 系统级错误
    UNKNOWN = "unknown"                  # 未知事件

    # --- 兼容性映射 (Backward Compatibility) ---
    PLAN_CREATED = "plan"
    EXECUTE_START = "execute_start"
    SUBTASK_DONE = "subtask_done"
    SUBTASK_FAILED = "subtask_failed"


@dataclass(slots=True)
class StreamEvent:
    """
    统一的 SSE 事件载体
    """
    type: str # 应该使用 StreamEventType.value
    content: Any = ""
    sub_type: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    status: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """安全序列化，确保 Enum 能够被正确处理"""
        return {
            "type": self.type.value if isinstance(self.type, Enum) else self.type,
            "content": self.content,
            "sub_type": self.sub_type,
            "data": self.data,
            "status": self.status
        }


class StreamState(Enum):
    """显式状态机定义，消除布尔标志位组合爆炸 (Primitive Obsession)"""
    NORMAL = auto()
    THINKING = auto()
    IN_BLOCK = auto()

# =============================================================================
# Adapter Implementation 
# =============================================================================
class AgnoStreamAdapter:
    """
    负责将底层模型引擎 (Agno) 的异构流数据，
    转换为标准的 StreamEvent 强类型流，并提供多维度的时序保证和性能观测。
    """
    
    # 动态前瞻窗口的基础哨兵集合
    SENTINELS: Set[str] = {"<think>", "</think>", ":::", "[clarify]:", "[plan]:", "[tool]:"}

    def __init__(self, extract_charts: bool = True):
        self.extract_charts = extract_charts
        self._buffer = ""
        self._state = StreamState.NORMAL
        self._block_type: Optional[str] = None
        
        # 动态计算前瞻窗口大小，避免触发词在边界被截断
        self._lookahead = max(len(s) for s in self.SENTINELS) + 5
        
        # 性能观测：工具调用耗时记录
        self._tool_timers: Dict[str, float] = {}

    async def _flush_buffer(self) -> AsyncGenerator[StreamEvent, None]:
        """安全排空缓冲区，增强异常中断的防御能力"""
        if not self._buffer:
            return
            
        if self._state == StreamState.IN_BLOCK:
            # 防御：处理块未闭合的异常情况
            logger.warning(f"Unclosed block '{self._block_type}' flushed.")
            yield self._handle_block(self._block_type, self._buffer)
        elif self._state == StreamState.THINKING:
            yield StreamEvent(type=StreamEventType.THINK_DELTA.value, content=self._buffer, status="running")
        else:
            yield StreamEvent(type=StreamEventType.TEXT_DELTA.value, content=self._buffer, status="streaming")
            
        self._buffer = ""
        self._state = StreamState.NORMAL
        self._block_type = None

    def _handle_block(self, btype: Optional[str], raw_content: str) -> StreamEvent:
        """处理提取出来的块内容"""
        btype = btype or "unknown"
        if btype in ("echarts", "d3", "antv") and self.extract_charts:
            try:
                data = json.loads(raw_content)
                return StreamEvent(type=StreamEventType.CHART_BLOCK.value, content=data, sub_type=btype, status="streaming")
            except json.JSONDecodeError as e:
                logger.warning(f"{btype} JSON parse failed: {e}")
                return StreamEvent(type=StreamEventType.TEXT_DELTA.value, content=f"\n```json\n{raw_content}\n```\n", status="streaming")
                
        if btype in ("audio", "video", "media"):
            try:
                data = json.loads(raw_content)
                return StreamEvent(type=StreamEventType.MEDIA_BLOCK.value, content=data, sub_type=btype, status="completed")
            except json.JSONDecodeError:
                # 兼容纯 URL 格式: ::: video \n https://... \n :::
                return StreamEvent(type=StreamEventType.MEDIA_BLOCK.value, content={"url": raw_content.strip(), "media_type": btype}, sub_type=btype, status="completed")
        
        return StreamEvent(type=StreamEventType.TEXT_DELTA.value, content=f"\n```{btype}\n{raw_content}\n```\n", status="streaming")

    def _safe_to_dict(self, obj: Any) -> Dict[str, Any]:
        if hasattr(obj, "to_dict") and callable(obj.to_dict):
            return obj.to_dict()
        return {}

    async def to_standard_events(self, chunk: Any) -> AsyncGenerator[StreamEvent, None]:
        try:
            # 1. 拦截底层引擎的特殊结构
            if type(chunk).__name__ == "RunOutput":
                async for out in self._flush_buffer():
                    yield out
                yield StreamEvent(type=StreamEventType.RUN_COMPLETED.value, data=self._safe_to_dict(chunk), status="completed")
                return

            if hasattr(chunk, "tool_calls") and chunk.tool_calls:
                async for out in self._flush_buffer():
                    yield out
                names = [tc.function.name for tc in chunk.tool_calls if getattr(tc, "function", None)]
                if names:
                    yield StreamEvent(type=StreamEventType.STATUS_UPDATE.value, content=f"正在运行工具: {', '.join(names)}...", status="running")

            # 2. 字典型事件映射 (字典流)
            if isinstance(chunk, dict) and "type" in chunk:
                t = chunk.get("type")
                
                # 在处理非内容事件前，清空文本缓冲区，确保时序正确
                if t not in ("content", "message", "final", StreamEventType.TEXT_DELTA.value):
                    async for out in self._flush_buffer():
                        yield out

                if t in ("reasoning", "thought", "thinking", "think", "reasoning_content", StreamEventType.THINK_DELTA.value):
                    val = chunk.get("content", "") or chunk.get("reasoning_content", "") or chunk.get(t, "")
                    yield StreamEvent(type=StreamEventType.THINK_DELTA.value, content=val, status="running")
                    return

                if t in ("tool_start", "tool_call", "tool_use", "call", StreamEventType.TOOL_CALL_START.value):
                    data = chunk.get("content") if isinstance(chunk.get("content"), dict) else chunk
                    tool_name = data.get("tool") or data.get("name") or "worker"
                    tool_call_id = data.get("tool_call_id", f"unknown_{time.time()}")
                    self._tool_timers[tool_call_id] = time.time()
                    
                    yield StreamEvent(
                        type=StreamEventType.TOOL_CALL_START.value,
                        content={
                            "tool_call_id": tool_call_id,
                            "tool": tool_name,
                            "args": data.get("args") or data.get("arguments") or {}
                        },
                        status="running"
                    )
                    return

                if t in ("tool_result", "tool_end", "result", StreamEventType.TOOL_CALL_END.value):
                    data = chunk.get("content") if isinstance(chunk.get("content"), dict) else chunk
                    tool_name = data.get("tool") or data.get("name")
                    output_data = data.get("result") or data.get("output")
                    tool_call_id = data.get("tool_call_id")
                    
                    latency = None
                    if tool_call_id and tool_call_id in self._tool_timers:
                        latency = round(time.time() - self._tool_timers.pop(tool_call_id), 3)
                    
                    # RAG Citation Interception: 拦截 search_knowledge_base 的返回，推送给前端用于渲染 Citation 锚点
                    if tool_name == "search_knowledge_base" and output_data:
                        # 假设 output_data 包含了召回的文档片段
                        # 我们将其封装为一个特殊的 citation 事件
                        yield StreamEvent(
                            type=StreamEventType.KNOWLEDGE_RETRIEVED.value,
                            content="知识库检索结果",
                            data={"chunks": output_data},
                            status="streaming"
                        )
                    
                    event_data = {"latency": latency} if latency is not None else None
                    yield StreamEvent(
                        type=StreamEventType.TOOL_CALL_END.value,
                        content={
                            "tool_call_id": tool_call_id,
                            "tool": tool_name,
                            "output": output_data
                        },
                        data=event_data,
                        status="completed"
                    )
                    return

                if t in ("content", StreamEventType.TEXT_DELTA.value):
                    content_val = chunk.get("content", "")
                    if isinstance(content_val, str):
                        async for out in self._process_content(content_val):
                            yield out
                    else:
                        yield StreamEvent(type=StreamEventType.TEXT_DELTA.value, content=str(content_val), status="streaming")
                    return
                
                if t in ("message", "final"):
                    msg = chunk.get("message") or chunk.get("final_message")
                    content_val = getattr(msg, "content", None) or str(msg)
                    async for out in self._process_content(content_val):
                        yield out
                    return

                yield StreamEvent(type=StreamEventType.UNKNOWN.value, content=chunk, status="streaming")
                return

            if isinstance(chunk, str):
                # Ensure we don't treat JSON strings that look like control frames as pure text if they somehow bypassed earlier layers
                # Only apply this if the string strongly looks like our internal SSE JSON
                if chunk.strip().startswith('{"type":') and '"status":' in chunk:
                    try:
                        parsed = json.loads(chunk)
                        async for out in self.to_standard_events(parsed):
                            yield out
                        return
                    except json.JSONDecodeError:
                        pass
                        
                async for out in self._process_content(chunk):
                    yield out
                return

            # 4. Agno/Pydantic 对象事件
            event_type = getattr(chunk, "event", None)
            if isinstance(event_type, str):
                # 拦截底层的工具调用事件，避免将其转换为文本输出污染对话流
                if event_type == "ToolCallStarted":
                    async for out in self._flush_buffer():
                        yield out
                    tool = getattr(chunk, "tool", None)
                    chunk_tools = getattr(chunk, "tools", []) or []
                    tools = list(chunk_tools) if isinstance(chunk_tools, (list, tuple)) else []
                    if tool and tool not in tools:
                        tools.append(tool)
                    if tools:
                        for tool_item in tools:
                            tool_call_id = getattr(tool_item, "tool_call_id", f"unknown_{time.time()}")
                            self._tool_timers[tool_call_id] = time.time()
                            yield StreamEvent(
                                type=StreamEventType.TOOL_CALL_START.value,
                                content={
                                    "tool_call_id": tool_call_id,
                                    "tool": getattr(tool_item, "tool_name", "worker"),
                                    "args": getattr(tool_item, "tool_args", {})
                                },
                                status="running"
                            )
                    return
                elif event_type in ("ToolCallCompleted", "ToolCallError"):
                    async for out in self._flush_buffer():
                        yield out
                    tool = getattr(chunk, "tool", None)
                    chunk_tools = getattr(chunk, "tools", []) or []
                    tools = list(chunk_tools) if isinstance(chunk_tools, (list, tuple)) else []
                    if tool and tool not in tools:
                        tools.append(tool)
                    if tools:
                        for tool_item in tools:
                            tool_name = getattr(tool_item, "tool_name", "worker")
                            output_data = getattr(tool_item, "result", "")
                            error_msg = getattr(tool_item, "tool_call_error", None)
                            tool_call_id = getattr(tool_item, "tool_call_id", None)
                            
                            latency = None
                            if tool_call_id and tool_call_id in self._tool_timers:
                                latency = round(time.time() - self._tool_timers.pop(tool_call_id), 3)
                            
                            # RAG Citation Interception (Agno Native Event)
                            if tool_name == "search_knowledge_base" and output_data and not error_msg:
                                yield StreamEvent(
                                    type=StreamEventType.KNOWLEDGE_RETRIEVED.value,
                                    content="知识库检索结果",
                                    data={"chunks": output_data},
                                    status="streaming"
                                )
                                
                            event_data = {"latency": latency} if latency is not None else None
                            yield StreamEvent(
                                type=StreamEventType.TOOL_CALL_END.value if not error_msg else StreamEventType.TOOL_CALL_ERROR.value,
                                content={
                                    "tool_call_id": tool_call_id,
                                    "tool": tool_name,
                                    "output": output_data,
                                    "is_error": bool(error_msg) or event_type == "ToolCallError",
                                    "logs": [error_msg] if error_msg else []
                                },
                                data=event_data,
                                status="completed"
                            )
                    return
                elif event_type in ("RunStarted", "RunCompleted", "ModelRequestStarted", "ModelRequestCompleted", "RunContentCompleted"):
                    # Safe to ignore these purely internal lifecycle events to prevent noise and duplicates
                    return
                elif event_type == "RunIntermediateContent":
                    pass # Continue to reasoning/content extraction below

            reasoning = getattr(chunk, "thinking", None) or getattr(chunk, "reasoning", None) or getattr(chunk, "reasoning_content", None)
            if isinstance(reasoning, str) and reasoning:
                yield StreamEvent(type=StreamEventType.THINK_DELTA.value, content=reasoning, status="running")
                return

            content = getattr(chunk, "content", None)
            if isinstance(content, str) and content:
                async for out in self._process_content(content):
                    yield out
                return

            if content is not None:
                yield StreamEvent(type=StreamEventType.TEXT_DELTA.value, content=str(content), status="streaming")

        except Exception as e:
            logger.error(f"Stream adapt failed: {e}", exc_info=True)
            yield StreamEvent(type=StreamEventType.ERROR.value, content="Stream processing error", status="failed")

    async def flush(self) -> AsyncGenerator[StreamEvent, None]:
        async for out in self._flush_buffer():
            yield out

    async def _process_content(self, text: str) -> AsyncGenerator[StreamEvent, None]:
        """状态机驱动的内容解析器，带动态前瞻窗口"""
        if not text:
            return

        self._buffer += text
        
        while self._buffer:
            if self._state == StreamState.NORMAL:
                think_start = self._buffer.find("<think>")
                block_start = self._buffer.find(":::")
                
                # Filter out internal intent tags at the start or after newlines
                intent_match = re.search(r'(?m)^\[(clarify|plan|tool|intent)\]:\s*', self._buffer)
                if intent_match:
                    if intent_match.start() > 0:
                        yield StreamEvent(type=StreamEventType.TEXT_DELTA.value, content=self._buffer[:intent_match.start()], status="streaming")
                    self._buffer = self._buffer[intent_match.end():]
                    continue
                
                # Check for <think> tag
                if think_start != -1:
                    if think_start > 0:
                        yield StreamEvent(type=StreamEventType.TEXT_DELTA.value, content=self._buffer[:think_start], status="streaming")
                    self._state = StreamState.THINKING
                    self._buffer = self._buffer[think_start + 7:]
                    continue
                    
                # Check for block tag :::
                if block_start != -1:
                    if block_start > 0:
                        yield StreamEvent(type=StreamEventType.TEXT_DELTA.value, content=self._buffer[:block_start], status="streaming")
                    
                    newline_pos = self._buffer.find("\n", block_start)
                    if newline_pos != -1:
                        block_header = self._buffer[block_start+3:newline_pos].strip()
                        self._block_type = block_header.split()[0] if block_header else "unknown"
                        self._state = StreamState.IN_BLOCK
                        self._buffer = self._buffer[newline_pos+1:]
                        continue
                    else:
                        # Wait for full block header
                        if len(self._buffer) - block_start < self._lookahead:
                            break
                            
                # Nothing found, flush safely
                if len(self._buffer) > self._lookahead:
                    safe_len = len(self._buffer) - self._lookahead
                    yield StreamEvent(type=StreamEventType.TEXT_DELTA.value, content=self._buffer[:safe_len], status="streaming")
                    self._buffer = self._buffer[safe_len:]
                break

            elif self._state == StreamState.THINKING:
                think_end = self._buffer.find("</think>")
                if think_end != -1:
                    content = self._buffer[:think_end]
                    if content:
                        yield StreamEvent(type=StreamEventType.THINK_DELTA.value, content=content, status="running")
                    self._state = StreamState.NORMAL
                    self._buffer = self._buffer[think_end + 8:]
                    continue
                else:
                    if len(self._buffer) > self._lookahead:
                        safe_len = len(self._buffer) - self._lookahead
                        yield StreamEvent(type=StreamEventType.THINK_DELTA.value, content=self._buffer[:safe_len], status="running")
                        self._buffer = self._buffer[safe_len:]
                    break

            elif self._state == StreamState.IN_BLOCK:
                block_end = self._buffer.find(":::")
                if block_end != -1:
                    content = self._buffer[:block_end]
                    if content:
                        yield self._handle_block(self._block_type, content)
                    self._state = StreamState.NORMAL
                    self._block_type = None
                    self._buffer = self._buffer[block_end + 3:]
                    # Skip trailing newline
                    if self._buffer.startswith("\n"):
                        self._buffer = self._buffer[1:]
                    continue
                else:
                    break

