import logging
import time
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class SystemMetricsService:
    def __init__(self):
        self._stats: Dict[str, Any] = {"events": []}

    def record(self, event: str, data: Dict[str, Any]):
        ts = time.time()
        item = {"event": event, "ts": ts, **data}
        self._stats["events"].append(item)
        try:
            logger.info(f"metric {event} {data}")
        except Exception:
            pass

    def get_stats(self) -> Dict[str, Any]:
        return self._stats


# Global instance
metrics_service = SystemMetricsService()


def record(event: str, data: Dict[str, Any]):
    """Helper for backward compatibility or ease of use"""
    metrics_service.record(event, data)


def get_stats() -> Dict[str, Any]:
    """Helper for backward compatibility"""
    return metrics_service.get_stats()
