import json
from typing import Any

def sse_pack(event: str, data: Any) -> str:
    """Format data as Server-Sent Event"""
    if isinstance(data, (dict, list)):
        data_str = json.dumps(data, ensure_ascii=False)
    else:
        data_str = str(data)
    
    # Handle multiline data
    lines = data_str.split('\n')
    formatted_data = '\n'.join([f"data: {line}" for line in lines])
    return f"event: {event}\n{formatted_data}\n\n"
