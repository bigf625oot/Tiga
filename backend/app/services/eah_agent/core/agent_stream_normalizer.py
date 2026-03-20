"""
事件流标准化器
场景：
    1. 前端需要根据事件类型渲染不同的 UI 组件
    2. 后端需要根据事件类型进行逻辑处理
"""
import logging
from typing import Any, AsyncGenerator, Dict
from enum import Enum

logger = logging.getLogger(__name__)

class ClaudeStyleType(str, Enum):
    THOUGHT = "thought"  # 思维链
    CALL = "call"        # 工具调用开始
    RESULT = "result"    # 工具结果返回
    TEXT = "text"        # 最终文本正文
    ERROR = "error"      # 错误信息

async def normalize_event_stream(stream: AsyncGenerator[Any, None]) -> AsyncGenerator[Dict[str, Any], None]:
    """
    将杂乱的事件流转换为 Claude Code 风格的标准流。
    前端可以直接根据 type 渲染不同的 UI 组件：
    - type == 'thought' -> 渲染在灰色折叠框内
    - type == 'call'    -> 渲染一个“正在调用工具...”的 Loading
    - type == 'result'  -> 渲染工具输出或直接隐藏
    - type == 'text'    -> 渲染打字机正文
    """
    
    # 状态追踪，处理文本流中的 <think> 标签逻辑
    state = {
        "is_thinking": False,
        "buffer": ""
    }

    async def _flush_buffer() -> AsyncGenerator[Dict[str, Any], None]:
        """将缓冲区中剩余的内容输出"""
        if state["buffer"]:
            if state["is_thinking"]:
                yield {"type": ClaudeStyleType.THOUGHT, "content": state["buffer"]}
            else:
                yield {"type": ClaudeStyleType.TEXT, "content": state["buffer"]}
            state["buffer"] = ""

    async def _process_content(content: str) -> AsyncGenerator[Dict[str, Any], None]:
        """处理文本内容，识别并分离 <think> 标签，支持跨 Chunk 断裂"""
        if not content:
            return

        state["buffer"] += content
        buffer = state["buffer"]

        while True:
            if not state["is_thinking"]:
                start_idx = buffer.find("<think>")
                if start_idx != -1:
                    if start_idx > 0:
                        yield {"type": ClaudeStyleType.TEXT, "content": buffer[:start_idx]}
                    state["is_thinking"] = True
                    buffer = buffer[start_idx + 7:]
                    continue
                else:
                    last_lt = buffer.rfind('<')
                    if last_lt == -1:
                        if buffer:
                            yield {"type": ClaudeStyleType.TEXT, "content": buffer}
                        buffer = ""
                        break
                    else:
                        potential = buffer[last_lt:]
                        if "<think>".startswith(potential):
                            if last_lt > 0:
                                yield {"type": ClaudeStyleType.TEXT, "content": buffer[:last_lt]}
                            buffer = potential
                            break
                        else:
                            if last_lt > 0:
                                yield {"type": ClaudeStyleType.TEXT, "content": buffer[:last_lt]}
                            buffer = buffer[last_lt:]
                            if not "<think>".startswith(buffer):
                                yield {"type": ClaudeStyleType.TEXT, "content": buffer}
                                buffer = ""
                            break
            else:
                end_idx = buffer.find("</think>")
                if end_idx != -1:
                    if end_idx > 0:
                        yield {"type": ClaudeStyleType.THOUGHT, "content": buffer[:end_idx]}
                    state["is_thinking"] = False
                    buffer = buffer[end_idx + 8:]
                    continue
                else:
                    last_lt = buffer.rfind('<')
                    if last_lt == -1:
                        if buffer:
                            yield {"type": ClaudeStyleType.THOUGHT, "content": buffer}
                        buffer = ""
                        break
                    else:
                        potential = buffer[last_lt:]
                        if "</think>".startswith(potential):
                            if last_lt > 0:
                                yield {"type": ClaudeStyleType.THOUGHT, "content": buffer[:last_lt]}
                            buffer = potential
                            break
                        else:
                            if last_lt > 0:
                                yield {"type": ClaudeStyleType.THOUGHT, "content": buffer[:last_lt]}
                            buffer = buffer[last_lt:]
                            if not "</think>".startswith(buffer):
                                yield {"type": ClaudeStyleType.THOUGHT, "content": buffer}
                                buffer = ""
                            break
        
        state["buffer"] = buffer

    async for item in stream:
        try:
            # 1. 纯文本处理
            if isinstance(item, str):
                async for chunk in _process_content(item):
                    yield chunk
                continue

            if not isinstance(item, dict):
                continue


            t = item.get("type")

            # 在处理非纯文本类型的事件前，先把缓冲区里的残留文本吐出
            if t not in ("content", "message", "final"):
                async for chunk in _flush_buffer():
                    yield chunk

            # 2. 显式思维链映射 (从 API 直接获取的情况)
            if t in ("reasoning", "thought", "thinking"):
                yield {"type": ClaudeStyleType.THOUGHT, "content": item.get("content", "")}

            # 3. 工具调用映射 (Claude Code 风格)
            elif t in ("tool_start", "tool_call", "tool_use"):
                data = item.get("content") if isinstance(item.get("content"), dict) else item
                yield {
                    "type": ClaudeStyleType.CALL,
                    "content": {
                        "tool": data.get("tool") or data.get("name") or "worker",
                        "args": data.get("args") or data.get("arguments") or {}
                    }
                }

            # 4. 工具结果映射
            elif t in ("tool_result", "tool_end"):
                data = item.get("content") if isinstance(item.get("content"), dict) else item
                yield {
                    "type": ClaudeStyleType.RESULT,
                    "content": {
                        "tool": data.get("tool") or data.get("name"),
                        "output": data.get("result") or data.get("output")
                    }
                }

            # 5. 正文内容映射
            elif t == "content":
                content = item.get("content", "")
                if isinstance(content, str):
                    async for chunk in _process_content(content):
                        yield chunk
                else:
                    yield {"type": ClaudeStyleType.TEXT, "content": str(content)}

            # 6. Message 对象兼容处理
            elif t in ("message", "final"):
                msg = item.get("message") or item.get("final_message")
                content = getattr(msg, "content", None) or str(msg)
                async for chunk in _process_content(content):
                    yield chunk

        except Exception as e:
            logger.error(f"Normalization failed for item {item}: {e}")
            yield {"type": ClaudeStyleType.ERROR, "content": "Stream processing error"}

    # 流结束时，清空残留的 buffer
    async for chunk in _flush_buffer():
        yield chunk