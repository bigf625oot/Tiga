import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def get_optimized_context(history: List[Dict[str, Any]], system_prompt: str = "", max_tokens: int = 4000) -> List[Dict[str, Any]]:
    """
    Optimize context window by keeping the system prompt and the most recent messages 
    that fit within the token limit.
    """
    optimized_history = []
    current_tokens = 0
    
    # 1. Estimate System Prompt Tokens (approx 4 chars/token)
    sys_tokens = len(system_prompt) // 4
    current_tokens += sys_tokens
    
    # 2. Iterate backwards through history
    # We want to keep the most recent messages
    for msg in reversed(history):
        content = str(msg.get("content", ""))
        # Rough estimation
        msg_tokens = len(content) // 4
        
        # Add some overhead for message structure
        msg_tokens += 4 
        
        if current_tokens + msg_tokens > max_tokens:
            logger.debug(f"Context limit reached. Dropping {len(history) - len(optimized_history)} old messages.")
            break
            
        optimized_history.insert(0, msg)
        current_tokens += msg_tokens
        
    return optimized_history
