import json
import logging
from typing import Any, Dict, List

from openai import OpenAI

logger = logging.getLogger(__name__)


def run_reasoning_tool_loop(
    *,
    client: OpenAI,
    model_id: str,
    user_prompt: str,
    tools: List[Dict[str, Any]],
    tool_call_map: Dict[str, Any],
    enable_thinking: bool = True,
    messages: List[Dict[str, Any]] = None,  # Add messages parameter for history
) -> Dict[str, Any]:
    if messages is None:
        messages = []

    # Append user prompt if provided and not already in messages (simple check)
    # Actually, caller should handle full history construction, but let's keep backward compatibility
    # If messages are passed, we assume they include history.
    # We need to ensure the LAST message is the user prompt.
    if user_prompt:
        # Check if last message is user prompt, if not append it
        if not messages or messages[-1].get("content") != user_prompt:
            messages.append({"role": "user", "content": user_prompt})

    while True:
        extra_body = {"thinking": {"type": "enabled"}} if enable_thinking else None

        # Log the request messages for debugging
        # logger.info(f"DeepSeek Request Messages: {json.dumps(messages, default=str)}")

        try:
            response = client.chat.completions.create(
                model=model_id, messages=messages, tools=tools or None, extra_body=extra_body
            )
        except Exception as e:
            # If 400 error about missing reasoning_content, it might be due to history manipulation?
            # Or maybe we need to ensure content is not None
            logger.error(f"DeepSeek API Error: {e}")
            raise e

        msg = response.choices[0].message

        # Convert ChatCompletionMessage to dict to ensure reasoning_content is preserved
        # DeepSeek requires reasoning_content to be passed back during tool loops
        msg_dict = {
            "role": msg.role,
            "content": msg.content or "",  # Ensure content is not None
        }

        if hasattr(msg, "tool_calls") and msg.tool_calls:
            msg_dict["tool_calls"] = msg.tool_calls

        # Explicitly handle reasoning_content
        # 1. Try direct attribute access (standard)
        rc = getattr(msg, "reasoning_content", None)
        # 2. Try extra_fields or dict access (if SDK puts it there)
        if not rc:
            try:
                # Attempt to access raw dict if available
                if hasattr(msg, "model_dump"):
                    raw = msg.model_dump()
                    rc = raw.get("reasoning_content")
                elif hasattr(msg, "to_dict"):
                    raw = msg.to_dict()
                    rc = raw.get("reasoning_content")
                elif hasattr(msg, "__dict__"):
                    rc = msg.__dict__.get("reasoning_content")
            except:
                pass

        if rc:
            msg_dict["reasoning_content"] = rc
        else:
            # If enable_thinking is True but we got no reasoning_content,
            # and it's a tool call, we might need to be careful.
            # But usually it's fine if the model didn't output it.
            pass

        messages.append(msg_dict)

        tool_calls = getattr(msg, "tool_calls", None) or []
        if not tool_calls:
            return {"final_message": msg, "messages": messages}
        for call in tool_calls:
            name = call.function.name
            args_str = call.function.arguments or "{}"
            try:
                args = json.loads(args_str)
            except Exception:
                args = {}
            fn = tool_call_map.get(name)
            if not fn:
                logger.warning(f"Tool not found: {name}")
                result = {"error": f"Unknown tool: {name}", "args": args}
            else:
                try:
                    logger.info(f"Executing tool: {name} with args: {args}")
                    result = fn(**args) if isinstance(args, dict) else fn(args)
                    logger.info(f"Tool {name} result: {str(result)[:500]}")
                except Exception as e:
                    logger.error(f"Tool {name} failed: {e}", exc_info=True)
                    result = {"error": str(e), "args": args}
            tool_msg = {"role": "tool", "content": json.dumps(result, ensure_ascii=False), "tool_call_id": call.id}
            messages.append(tool_msg)
