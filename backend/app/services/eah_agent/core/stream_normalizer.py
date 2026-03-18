from typing import Any, AsyncGenerator, Dict

from app.services.eah_agent.core.stream_processor import parse_thinking_stream


async def normalize_event_stream(stream: AsyncGenerator[Any, None]) -> AsyncGenerator[Dict[str, Any], None]:
    async def _adapter() -> AsyncGenerator[Any, None]:
        async for item in stream:
            if isinstance(item, dict) and "type" in item:
                t = item.get("type")

                if t == "reasoning":
                    yield f"<think>{item.get('content', '')}</think>"
                    continue

                if t == "tool_start":
                    yield {"type": "tool_start", "content": {"tool": item.get("tool"), "args": item.get("args")}}
                    continue

                if t == "tool_result":
                    yield {"type": "tool_end", "content": {"tool": item.get("tool"), "result": item.get("result")}}
                    continue

                if t == "message":
                    msg = item.get("message")
                    content = getattr(msg, "content", None)
                    if content:
                        yield str(content)
                    continue

                if t == "final":
                    msg = item.get("final_message")
                    content = getattr(msg, "content", None)
                    if content:
                        yield str(content)
                    continue

                if "content" not in item:
                    item["content"] = item.get("data", "")

                yield item
            else:
                yield item

    async for chunk in parse_thinking_stream(_adapter()):
        yield chunk

