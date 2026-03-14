import logging
from typing import AsyncGenerator, Dict, Any

logger = logging.getLogger(__name__)

async def parse_thinking_stream(stream: AsyncGenerator[Any, None]) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Robust stream parser for <think>...</think> blocks.
    Handles split tags across chunks correctly.
    Passthrough for non-string chunks (like tool events).
    
    Standardized Output Format:
    {
        "type": "content" | "think" | "status" | "error",
        "content": str | dict
    }
    """
    buffer = ""
    in_think = False
    
    async for chunk in stream:
        # Passthrough non-string events (assuming they are already dicts or objects we want to yield)
        if not isinstance(chunk, str):
            # Flush buffer if any
            if buffer:
                if in_think:
                    yield {"type": "think", "content": buffer}
                else:
                    yield {"type": "content", "content": buffer}
                buffer = ""
            
            # If chunk is already a dict with 'type', pass it through
            if isinstance(chunk, dict) and "type" in chunk:
                yield chunk
            else:
                # Wrap unknown objects in status or content?
                # For now, assume it's status or similar event
                yield {"type": "status", "content": chunk}
            continue

        buffer += chunk
        
        while True:
            if not in_think:
                # Look for <think>
                start_idx = buffer.find("<think>")
                if start_idx != -1:
                    # Found start tag
                    # Yield content before tag
                    if start_idx > 0:
                        yield {"type": "content", "content": buffer[:start_idx]}
                    
                    in_think = True
                    buffer = buffer[start_idx + 7:] # Skip <think>
                    continue # Loop to check for end tag in remaining buffer
                else:
                    # No start tag found yet.
                    # Check if buffer ends with partial tag <, <t, <th, <thi, <thin, <think
                    
                    # Optimization: find last '<'
                    last_lt = buffer.rfind('<')
                    if last_lt == -1:
                        # No potential tag start
                        if buffer:
                            yield {"type": "content", "content": buffer}
                        buffer = ""
                        break
                    else:
                        # Potential tag start found at last_lt
                        # Check if it matches prefix of <think>
                        potential = buffer[last_lt:]
                        if "<think>".startswith(potential):
                            # It is a prefix, keep it and yield before it
                            if last_lt > 0:
                                yield {"type": "content", "content": buffer[:last_lt]}
                            buffer = potential
                            break
                        else:
                            # Not a valid prefix, yield up to last_lt
                            if last_lt > 0:
                                yield {"type": "content", "content": buffer[:last_lt]}
                            buffer = buffer[last_lt:]
                            # Check if buffer matches partial <think> start?
                            # If not, yield it too.
                            if not "<think>".startswith(buffer):
                                 yield {"type": "content", "content": buffer}
                                 buffer = ""
                            break
            
            else: # Inside <think>
                # Look for </think>
                end_idx = buffer.find("</think>")
                if end_idx != -1:
                    # Found end tag
                    # Yield think content before tag
                    if end_idx > 0:
                        yield {"type": "think", "content": buffer[:end_idx]}
                    
                    in_think = False
                    buffer = buffer[end_idx + 8:] # Skip </think>
                    continue # Loop to check for start tag in remaining buffer
                else:
                    # No end tag found yet.
                    # Check partial end tag </think>
                    last_lt = buffer.rfind('<')
                    if last_lt == -1:
                        if buffer:
                            yield {"type": "think", "content": buffer}
                        buffer = ""
                        break
                    else:
                        potential = buffer[last_lt:]
                        if "</think>".startswith(potential):
                            if last_lt > 0:
                                yield {"type": "think", "content": buffer[:last_lt]}
                            buffer = potential
                            break
                        else:
                            # Not a closing tag prefix
                            if last_lt > 0:
                                yield {"type": "think", "content": buffer[:last_lt]}
                            buffer = buffer[last_lt:]
                            if not "</think>".startswith(buffer):
                                 yield {"type": "think", "content": buffer}
                                 buffer = ""
                            break

    # Flush remaining
    if buffer:
        if in_think:
            # Stream ended inside think block, treat as think content
            yield {"type": "think", "content": buffer}
        else:
            yield {"type": "content", "content": buffer}
