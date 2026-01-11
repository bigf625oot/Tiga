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
    enable_thinking: bool = True
) -> Dict[str, Any]:
    messages: List[Dict[str, Any]] = [{"role": "user", "content": user_prompt}]
    while True:
        extra_body = {"thinking": {"type": "enabled"}} if enable_thinking else None
        response = client.chat.completions.create(
            model=model_id,
            messages=messages,
            tools=tools or None,
            extra_body=extra_body
        )
        msg = response.choices[0].message
        messages.append(msg)
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
                result = {"error": f"Unknown tool: {name}", "args": args}
            else:
                try:
                    result = fn(**args) if isinstance(args, dict) else fn(args)
                except Exception as e:
                    result = {"error": str(e), "args": args}
            tool_msg = {
                "role": "tool",
                "content": json.dumps(result, ensure_ascii=False),
                "tool_call_id": call.id
            }
            messages.append(tool_msg)
