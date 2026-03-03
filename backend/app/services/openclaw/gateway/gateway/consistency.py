"""
Gateway Consistency Check & Compensation

Handles dirty data detection (Checksum, Version Mismatch, Out-of-order) and triggers compensation logic.
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime
from app.models.node import Node, NodeStatus
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from sqlalchemy import update, select

logger = logging.getLogger("openclaw.gateway.consistency")

class ConsistencyManager:
    """
    Manages data consistency checks and compensation actions.
    """
    def __init__(self):
        self.audit_log: List[Dict[str, Any]] = [] # In-memory buffer or send to ELK
        self.max_audit_log_size = 1000

    async def handle_dirty_data(self, node_id: str, payload: Dict[str, Any]):
        """
        Triggered when consistency check fails.
        1. Mark node as STALE/DIRTY.
        2. Log audit event.
        3. Trigger full sync (Compensation).
        """
        logger.warning(f"Detected dirty data from node {node_id}. Triggering compensation.")
        
        # 1. Audit Log
        event = {
            "node_id": node_id,
            "timestamp": datetime.now(),
            "reason": "checksum_mismatch" if payload.get("checksum") else "unknown",
            "payload_snippet": str(payload)[:100]
        }
        self.audit_log.append(event)
        if len(self.audit_log) > self.max_audit_log_size:
            self.audit_log.pop(0)

        # 2. Update DB Status (Async)
        async with AsyncSessionLocal() as db:
            try:
                # Mark as Offline/Stale to prevent dispatch
                await db.execute(
                    update(Node)
                    .where(Node.id == node_id)
                    .values(status=NodeStatus.OFFLINE, error_log=f"Dirty Data detected at {datetime.now()}")
                )
                await db.commit()
            except Exception as e:
                logger.error(f"Failed to update node status for dirty data: {e}")

        # 3. Trigger Full Sync Command
        # Send WS command to node: "force_sync"
        from .ws_handler import ws_manager
        if node_id in ws_manager.active_connections:
            ws = ws_manager.active_connections[node_id]
            try:
                cmd = {
                    "action": "force_sync",
                    "reason": "consistency_check_failed",
                    "timestamp": datetime.now().isoformat()
                }
                await ws.send_json(cmd)
                logger.info(f"Sent force_sync command to {node_id}")
            except Exception as e:
                logger.error(f"Failed to send sync command to {node_id}: {e}")

consistency_manager = ConsistencyManager()
