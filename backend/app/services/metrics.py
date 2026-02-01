from typing import Dict, Any
import time
import logging

logger = logging.getLogger(__name__)
_stats: Dict[str, Any] = {"events": []}

def record(event: str, data: Dict[str, Any]):
    ts = time.time()
    item = {"event": event, "ts": ts, **data}
    _stats["events"].append(item)
    try:
        logger.info(f"metric {event} {data}")
    except Exception:
        pass

def get_stats() -> Dict[str, Any]:
    return _stats
