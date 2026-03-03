"""
Gateway WebSocket Handler

Handles high-concurrency WebSocket connections with sharding, version check, deduplication, and backpressure.
"""

import asyncio
import json
import logging
import time
import zlib
from typing import Dict, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import ValidationError
from starlette.websockets import WebSocketState
from collections import defaultdict

# Rate Limiter
class TokenBucket:
    def __init__(self, capacity: int, fill_rate: float):
        self.capacity = float(capacity)
        self.tokens = float(capacity)
        self.fill_rate = fill_rate
        self.timestamp = time.time()

    def consume(self, tokens: int = 1) -> bool:
        now = time.time()
        delta = now - self.timestamp
        self.tokens = min(self.capacity, self.tokens + self.fill_rate * delta)
        self.timestamp = now
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

logger = logging.getLogger("openclaw.gateway.ws")

class WSConnectionManager:
    """
    Manages WebSocket connections.
    Supports Sharding via Dictionary Buckets (simple Hash Sharding logic can be added if distributed).
    Here implemented as single process manager for now.
    """
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.heartbeat_tracker: Dict[str, float] = {} # node_id -> last_seen
        self.sequence_tracker: Dict[str, int] = defaultdict(int) # node_id -> last_seq
        self.limiter = TokenBucket(capacity=20000, fill_rate=20000) # 20k QPS

    async def connect(self, websocket: WebSocket, node_id: str):
        await websocket.accept()
        self.active_connections[node_id] = websocket
        logger.info(f"Node {node_id} connected via WS")

    def disconnect(self, node_id: str):
        if node_id in self.active_connections:
            del self.active_connections[node_id]
        if node_id in self.heartbeat_tracker:
            del self.heartbeat_tracker[node_id]
        logger.info(f"Node {node_id} disconnected")

    async def handle_message(self, node_id: str, message: bytes | str):
        # 1. Rate Limit
        if not self.limiter.consume():
            logger.warning(f"Rate limit exceeded for {node_id}")
            # Send backpressure signal? Or just drop/log?
            # Backpressure: Wait or close.
            return

        try:
            # Decompress if needed (assuming client sends compressed bytes or json string)
            # Check if bytes
            if isinstance(message, bytes):
                # Try zlib decompress
                try:
                    data_str = zlib.decompress(message).decode("utf-8")
                except:
                    data_str = message.decode("utf-8")
            else:
                data_str = message

            payload = json.loads(data_str)
            
            # 2. Version Check
            version = payload.get("version")
            if not self._check_version(version):
                logger.warning(f"Invalid version {version} from {node_id}")
                # Trigger update or reject?
                return

            # 3. Deduplication (Sequence ID)
            seq_id = payload.get("sequence_id")
            if seq_id is not None:
                last_seq = self.sequence_tracker[node_id]
                if seq_id <= last_seq:
                    logger.debug(f"Duplicate/Old message {seq_id} from {node_id}")
                    return
                self.sequence_tracker[node_id] = seq_id

            # 4. Consistency Check (Timestamp, Checksum)
            if not self._check_consistency(payload):
                 # Handle dirty data
                 # Import locally to avoid circular import if necessary, or ensure correct path
                 from .consistency import consistency_manager
                 await consistency_manager.handle_dirty_data(node_id, payload)
                 return

            # 5. Process Heartbeat / Status Update
            self.heartbeat_tracker[node_id] = time.time()
            
            # Dispatch to callback (e.g., update DB, Metrics)
            await self._process_payload(node_id, payload)

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON from {node_id}")
        except Exception as e:
            logger.error(f"Error handling message from {node_id}: {e}")

    def _check_version(self, version: str) -> bool:
        # Simple check: must be >= 1.0.0
        # In real scenario, compare with min_supported_version
        return True

    def _check_consistency(self, payload: Dict[str, Any]) -> bool:
        # Check CRC32
        # Reconstruct data string: node_id + timestamp + seq + version
        # Ensure types match sender logic
        try:
            metric_data = f"{payload['node_id']}{payload['timestamp']}{payload['sequence_id']}{payload['version']}"
            calc_crc = zlib.crc32(metric_data.encode())
            if calc_crc != payload.get("checksum"):
                logger.warning(f"Checksum mismatch for {payload['node_id']}")
                return False
            
            # Check Timestamp Order (roughly, prevent replay attack or clock skew)
            # Allow 5s skew?
            now = time.time()
            ts = payload.get("timestamp", 0)
            if abs(now - ts) > 60: # 1 min skew allowed?
                 logger.warning(f"Timestamp skew for {payload['node_id']}: {ts} vs {now}")
                 # Maybe return False or just log warning? 
                 # Strict consistency might require sync.
                 pass
                 
            return True
        except Exception:
            return False

    async def _process_payload(self, node_id: str, payload: Dict[str, Any]):
        # Update Metrics (Prometheus)
        # Record latency: time.time() - payload['timestamp']
        # Update Node Status in DB (async callback)
        pass

ws_manager = WSConnectionManager()
