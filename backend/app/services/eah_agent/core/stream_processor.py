import logging
from typing import AsyncGenerator, Dict, Any

logger = logging.getLogger(__name__)

async def parse_thinking_stream(stream: AsyncGenerator[str, None]) -> AsyncGenerator[Dict[str, str], None]:
    """
    Robust stream parser for <think>...</think> blocks.
    Handles split tags across chunks correctly.
    """
    buffer = ""
    in_think = False
    
    async for chunk in stream:
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
                    # Max length 6 chars needed to match <think (length 6) before fully matched at 7
                    # Actually check for partial match logic:
                    # If buffer ends with a potential start of <think>, keep it.
                    # Otherwise yield.
                    
                    # Optimization: find last '<'
                    last_lt = buffer.rfind('<')
                    if last_lt == -1:
                        # No potential tag start
                        if buffer:
                            yield {"type": "content", "content": buffer}
                        buffer = ""
                    else:
                        # Potential tag start found at last_lt
                        # Check if it matches prefix of <think>
                        potential = buffer[last_lt:]
                        if "<think>".startswith(potential):
                            # It is a prefix, keep it and yield before it
                            if last_lt > 0:
                                yield {"type": "content", "content": buffer[:last_lt]}
                            buffer = potential
                        else:
                            # Not a valid prefix, but might be just text like "<b"
                            # If we are sure it's not <think>, we can yield.
                            # But wait, what if it's "<t"?
                            # So strictly check if it starts with any valid tag prefix?
                            # Or just yield up to last_lt and keep potential?
                            # To be safe, keep from last_lt.
                            if last_lt > 0:
                                yield {"type": "content", "content": buffer[:last_lt]}
                            buffer = buffer[last_lt:]
                    break # Get next chunk
            
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
                    else:
                        potential = buffer[last_lt:]
                        if "</think>".startswith(potential):
                            if last_lt > 0:
                                yield {"type": "think", "content": buffer[:last_lt]}
                            buffer = potential
                        else:
                            # Not a closing tag prefix
                            if last_lt > 0:
                                yield {"type": "think", "content": buffer[:last_lt]}
                            buffer = buffer[last_lt:]
                    break # Get next chunk

    # Flush remaining
    if buffer:
        if in_think:
            # Stream ended inside think block, treat as think content
            yield {"type": "think", "content": buffer}
        else:
            yield {"type": "content", "content": buffer}
