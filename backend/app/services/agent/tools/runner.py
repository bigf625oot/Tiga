import json
import logging
import inspect
from typing import Any, Dict, List, Union

import asyncio
from openai import AsyncOpenAI, OpenAI

logger = logging.getLogger(__name__)


async def _run_reasoning_tool_loop_async(
    *,
    client: Union[OpenAI, AsyncOpenAI],
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
    if user_prompt:
        # Check if last message is user prompt, if not append it
        if not messages or messages[-1].get("content") != user_prompt:
            messages.append({"role": "user", "content": user_prompt})

    while True:
        extra_body = {"thinking": {"type": "enabled"}} if enable_thinking else None

        try:
            # Support both Sync and Async clients
            if isinstance(client, AsyncOpenAI):
                response = await client.chat.completions.create(
                    model=model_id, messages=messages, tools=tools or None, extra_body=extra_body
                )
            else:
                # Fallback for sync client (blocking)
                response = client.chat.completions.create(
                    model=model_id, messages=messages, tools=tools or None, extra_body=extra_body
                )
        except Exception as e:
            logger.error(f"DeepSeek API Error: {e}")
            raise e

        msg = response.choices[0].message

        # Convert ChatCompletionMessage to dict to ensure reasoning_content is preserved
        msg_dict = {
            "role": msg.role,
            "content": msg.content or "",  # Ensure content is not None
        }

        if hasattr(msg, "tool_calls") and msg.tool_calls:
            msg_dict["tool_calls"] = msg.tool_calls

        # Explicitly handle reasoning_content
        rc = getattr(msg, "reasoning_content", None)
        if not rc:
            try:
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
                    
                    # Execute tool (Async or Sync)
                    if inspect.iscoroutinefunction(fn):
                        if isinstance(args, dict):
                            result = await fn(**args)
                        else:
                            result = await fn(args)
                    else:
                        # If we are in an async loop but fn is sync, it blocks.
                        # Ideally we should run sync tools in thread if we want to be non-blocking.
                        # But here we just call it.
                        result = fn(**args) if isinstance(args, dict) else fn(args)
                        
                    logger.info(f"Tool {name} result: {str(result)[:500]}")
                except Exception as e:
                    logger.error(f"Tool {name} failed: {e}", exc_info=True)
                    result = {"error": str(e), "args": args}
            tool_msg = {"role": "tool", "content": json.dumps(result, ensure_ascii=False), "tool_call_id": call.id}
            messages.append(tool_msg)


def run_reasoning_tool_loop(
    *,
    client: Union[OpenAI, AsyncOpenAI],
    model_id: str,
    user_prompt: str,
    tools: List[Dict[str, Any]],
    tool_call_map: Dict[str, Any],
    enable_thinking: bool = True,
    messages: List[Dict[str, Any]] = None,
) -> Dict[str, Any] | asyncio.Future:
    try:
        asyncio.get_running_loop()
        return _run_reasoning_tool_loop_async(
            client=client,
            model_id=model_id,
            user_prompt=user_prompt,
            tools=tools,
            tool_call_map=tool_call_map,
            enable_thinking=enable_thinking,
            messages=messages,
        )
    except RuntimeError:
        return asyncio.run(
            _run_reasoning_tool_loop_async(
                client=client,
                model_id=model_id,
                user_prompt=user_prompt,
                tools=tools,
                tool_call_map=tool_call_map,
                enable_thinking=enable_thinking,
                messages=messages,
            )
        )
