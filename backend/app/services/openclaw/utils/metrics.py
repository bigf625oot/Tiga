import time
from typing import Dict, Any, Optional
from prometheus_client import Counter, Histogram

# Prometheus Metrics
DISPATCH_TOTAL = Counter(
    "dispatch_total", 
    "Total task dispatch attempts",
    ["status"]
)

DISPATCH_FAIL_REASON = Counter(
    "dispatch_fail_reason",
    "Dispatch failure reasons",
    ["reason"]
)

DISPATCH_LATENCY = Histogram(
    "dispatch_latency_seconds",
    "Task dispatch latency",
    buckets=[0.1, 0.5, 1.0, 3.0, 6.0, 10.0]
)

class DispatchMetrics:
    """下发服务监控指标"""
    
    @staticmethod
    def record_dispatch(status: str):
        DISPATCH_TOTAL.labels(status=status).inc()

    @staticmethod
    def record_fail_reason(reason: str):
        DISPATCH_FAIL_REASON.labels(reason=reason).inc()

    @staticmethod
    def observe_latency(start_time: float):
        DISPATCH_LATENCY.observe(time.time() - start_time)
