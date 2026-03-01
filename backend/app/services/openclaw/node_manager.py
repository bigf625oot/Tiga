import logging
import json
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.node import Node, NodeMetric, Alert, NodeStatus, AlertLevel, AlertStatus
from app.models.task import SubTask
from app.schemas.node import NodeCreate, NodeUpdate, NodeMetricCreate
from app.services.openclaw import OpenClawService
from app.core.config import settings

logger = logging.getLogger(__name__)

class NodeManager:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        # Initialize service
        self.openclaw_service = None
        if settings.OPENCLAW_BASE_URL:
            self.openclaw_service = OpenClawService()

    async def get_nodes(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Node]:
        result = await db.execute(select(Node).offset(skip).limit(limit))
        return result.scalars().all()

    async def get_node(self, db: AsyncSession, node_id: str) -> Optional[Node]:
        result = await db.execute(select(Node).filter(Node.id == node_id))
        return result.scalars().first()

    async def register_node(self, db: AsyncSession, node_in: NodeCreate) -> Node:
        # Check duplicate name
        result = await db.execute(select(Node).filter(Node.name == node_in.name))
        existing_node = result.scalars().first()
        
        if existing_node:
            # Update existing
            update_data = node_in.dict(exclude_unset=True)
            for key, value in update_data.items():
                setattr(existing_node, key, value)
            existing_node.status = NodeStatus.ONLINE
            existing_node.last_heartbeat = datetime.now()
            await db.commit()
            await db.refresh(existing_node)
            return existing_node

        db_node = Node(
            **node_in.dict(),
            status=NodeStatus.ONLINE,
            last_heartbeat=datetime.now()
        )
        db.add(db_node)
        await db.commit()
        await db.refresh(db_node)
        return db_node

    async def heartbeat(self, db: AsyncSession, node_id: str, metrics: Optional[NodeMetricCreate] = None) -> Optional[Node]:
        result = await db.execute(select(Node).filter(Node.id == node_id))
        node = result.scalars().first()
        if not node:
            logger.warning(f"Heartbeat from unknown node {node_id}")
            return None

        node.last_heartbeat = datetime.now()
        if node.status == NodeStatus.OFFLINE or node.status == NodeStatus.ERROR:
             node.status = NodeStatus.ONLINE
        
        if metrics:
            db_metric = NodeMetric(
                node_id=node_id,
                **metrics.dict()
            )
            db.add(db_metric)
            
            # Check for alerts
            await self._check_metrics_for_alerts(db, node, metrics)

        await db.commit()
        await db.refresh(node)
        return node

    async def _check_metrics_for_alerts(self, db: AsyncSession, node: Node, metrics: NodeMetricCreate):
        # Latency > 1000ms -> P1
        if metrics.latency and metrics.latency > 1000:
            await self.create_alert(db, node.id, AlertLevel.P1, f"High Latency: {metrics.latency:.0f}ms")
            
        # Packet Loss > 10% -> P1
        if metrics.packet_loss and metrics.packet_loss > 10:
            await self.create_alert(db, node.id, AlertLevel.P1, f"Packet Loss: {metrics.packet_loss:.1f}%")

        # CPU > 90% -> P1
        if metrics.cpu_usage > 90:
            await self.create_alert(db, node.id, AlertLevel.P1, f"High CPU usage: {metrics.cpu_usage}%")
        
        # Memory > 90% -> P1
        if metrics.memory_usage > 90:
            await self.create_alert(db, node.id, AlertLevel.P1, f"High Memory usage: {metrics.memory_usage}%")
            
        # Disk > 95% -> P1
        if metrics.disk_usage > 95:
            await self.create_alert(db, node.id, AlertLevel.P1, f"High Disk usage: {metrics.disk_usage}%")

    async def create_alert(self, db: AsyncSession, node_id: str, level: AlertLevel, message: str):
        # Check if active alert exists to avoid spam
        # Only check for alerts created in last 5 minutes with same message
        five_mins_ago = datetime.now() - timedelta(minutes=5)
        result = await db.execute(select(Alert).filter(
            Alert.node_id == node_id, 
            Alert.message == message,
            Alert.status == AlertStatus.ACTIVE,
            Alert.created_at > five_mins_ago
        ))
        if result.scalars().first():
            return

        alert = Alert(node_id=node_id, level=level, message=message)
        db.add(alert)
        await db.commit()

    async def check_nodes_health(self, db: AsyncSession):
        # Find nodes with last_heartbeat > 30s
        threshold = datetime.now() - timedelta(seconds=30)
        result = await db.execute(select(Node).filter(
            Node.last_heartbeat < threshold,
            Node.status == NodeStatus.ONLINE
        ))
        nodes_down = result.scalars().all()
        
        for node in nodes_down:
            logger.warning(f"Node {node.id} ({node.name}) detected OFFLINE")
            node.status = NodeStatus.OFFLINE
            await self.create_alert(db, node.id, AlertLevel.P0, "Node offline (Heartbeat timeout)")
            
            # Failover logic: Reschedule active tasks
            # Find running subtasks assigned to this node
            subtasks_res = await db.execute(select(SubTask).filter(
                SubTask.worker_id == node.id,
                SubTask.status.in_(["RUNNING", "QUEUED"])
            ))
            active_subtasks = subtasks_res.scalars().all()
            
            for task in active_subtasks:
                logger.info(f"Rescheduling subtask {task.id} from failed node {node.id}")
                task.status = "PENDING" # Reset to PENDING to be picked up by another node
                task.worker_id = None
                # task.retry_count += 1 # SubTask model does not have retry_count yet, skipping

                # Optional: Add log entry
            
        await db.commit()

    async def sync_from_gateway(self, db: AsyncSession):
        """
        Sync nodes from OpenClaw Gateway.
        This allows us to discover nodes that are connected to the Gateway but not yet in our DB.
        """
        if not self.openclaw_service:
            return

        try:
            nodes_data = await self.openclaw_service.list_nodes()
            
            # log debug response structure
            logger.debug(f"Sync nodes response: {len(nodes_data)} nodes found")
            
            for n in nodes_data:
                node_id = n.id
                if not node_id: continue
                
                # Check existence
                result = await db.execute(select(Node).filter(Node.id == node_id))
                existing = result.scalars().first()
                
                if existing:
                    # Update existing node status
                    status_str = str(n.status).lower()
                    if status_str in ["connected", "online", "active"]:
                        existing.status = NodeStatus.ONLINE
                    elif status_str in ["disconnected", "offline"]:
                        existing.status = NodeStatus.OFFLINE
                    
                    existing.last_heartbeat = datetime.now()
                    # Update other fields if available
                    if n.name: existing.name = n.name
                    if n.version: existing.version = n.version
                    if n.platform: existing.platform = n.platform
                    
                else:
                    new_node = Node(
                        id=node_id,
                        name=n.name or f"Node-{node_id[:8]}",
                        platform=n.platform or "unknown",
                        status=NodeStatus.ONLINE, # Assume online if listed
                        version=n.version,
                        ip_address=n.address, 
                        last_heartbeat=datetime.now()
                    )
                    db.add(new_node)
            
            await db.commit()

        except Exception as e:
            logger.error(f"Sync failed: {e}")

    async def update_node_group(self, db: AsyncSession, node_id: str, group: str) -> Optional[Node]:
        node = await self.get_node(db, node_id)
        if not node:
            return None
        node.group = group
        await db.commit()
        await db.refresh(node)
        return node

    async def update_node_tags(self, db: AsyncSession, node_id: str, tags: List[str]) -> Optional[Node]:
        node = await self.get_node(db, node_id)
        if not node:
            return None
        node.tags = tags
        await db.commit()
        await db.refresh(node)
        return node

    async def dispatch_command(
        self, 
        db: AsyncSession, 
        command: str, 
        params: Dict[str, Any], 
        target_nodes: Optional[List[str]] = None,
        target_group: Optional[str] = None,
        target_tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Dispatch a command to multiple nodes based on filters.
        """
        from app.services.openclaw.node_monitor import node_monitor
        
        if not node_monitor.running or not node_monitor.client.is_connected:
             return {"status": "error", "message": "WebSocket client not connected"}

        # 1. Resolve target nodes
        query = select(Node).filter(Node.status == NodeStatus.ONLINE)
        
        if target_nodes:
            query = query.filter(Node.id.in_(target_nodes))
        
        if target_group:
            query = query.filter(Node.group == target_group)
            
        # For tags, we need to filter in python or use specific PG operators if using JSONB
        # Assuming simple JSON list for now, we'll fetch and filter if tags are specified
        
        result = await db.execute(query)
        candidates = result.scalars().all()
        
        final_targets = []
        if target_tags:
            for node in candidates:
                node_tags = node.tags or []
                # Check if node has ALL target tags (AND logic)
                if all(tag in node_tags for tag in target_tags):
                    final_targets.append(node)
        else:
            final_targets = candidates
            
        if not final_targets:
            return {"status": "warning", "message": "No online nodes found matching criteria", "count": 0}

        # 2. Execute in parallel
        async def _send(node):
            try:
                # node.invoke payload structure
                payload = {
                    "nodeId": node.id,
                    "command": command,
                    "params": params
                }
                res = await node_monitor.client.request("node.invoke", payload, timeout=5.0)
                return {"id": node.id, "status": "sent", "result": res}
            except Exception as e:
                return {"id": node.id, "status": "failed", "error": str(e)}

        tasks = [_send(node) for node in final_targets]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        success_count = 0
        details = []
        for res in batch_results:
            if isinstance(res, dict) and res.get("status") == "sent":
                success_count += 1
            details.append(res)

        return {
            "status": "success", 
            "total": len(final_targets),
            "sent": success_count,
            "details": details
        }

node_manager = NodeManager.get_instance()
