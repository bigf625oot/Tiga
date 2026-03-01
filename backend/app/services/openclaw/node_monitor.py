import asyncio
import logging
import time
from typing import Dict, Optional

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.node import Node, NodeStatus
from app.schemas.node import NodeMetricCreate
from app.services.openclaw.node_manager import node_manager
from app.services.openclaw.ws_client import OpenClawWsClient

logger = logging.getLogger(__name__)


class NodeMonitor:
    _instance = None
 
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
 
    def __init__(self):
        self.running = False
        
        # Use the unified OpenClaw WS Client
        self.client = OpenClawWsClient(client_id="node-monitor", mode="backend")
        self.client.on_connect = self._on_connect
        
        # Stats cache: {node_id: {pings: int, failures: int, total_rtt: float, last_check: datetime}}
        self.stats: Dict[str, Dict] = {} 

    async def start(self):
        if not settings.OPENCLAW_BASE_URL:
            logger.warning("OPENCLAW_BASE_URL not set, node monitor disabled")
            return
        
        if self.running:
            return
 
        self.running = True
        logger.info("Starting NodeMonitor service...")
        
        # Start connection loop
        asyncio.create_task(self._run_loop())
 
    async def stop(self):
        self.running = False
        await self.client.disconnect()
        logger.info("Stopping NodeMonitor service...")
 
    async def _run_loop(self):
        """Main loop that maintains connection and periodic checks."""
        while self.running:
            if not self.client.is_connected:
                try:
                    connected = await self.client.connect()
                    if not connected:
                        await asyncio.sleep(5) # Retry delay
                        continue
                except Exception as e:
                    logger.error(f"Connection failed: {e}")
                    await asyncio.sleep(5)
                    continue
            
            # If connected, perform checks
            try:
                start_time = time.time()
                await self._check_nodes()
                
                # Sleep for remaining time (e.g., 10s interval)
                elapsed = time.time() - start_time
                sleep_time = max(1.0, 10.0 - elapsed)
                await asyncio.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                await asyncio.sleep(5)

    async def _on_connect(self):
        """Callback when client connects successfully."""
        logger.info("NodeMonitor connected to Gateway, ready to check nodes.")

    async def _check_nodes(self):
        """
        Perform node checks:
        1. Fetch list of nodes from Gateway
        2. Update DB with node status
        3. For online nodes, send 'ping' to measure RTT
        """
        try:
            # 1. List Nodes using Client
            nodes_data = await self.client.request("node.list", {})
            
            if not isinstance(nodes_data, dict):
                logger.error(f"Unexpected node.list response: {type(nodes_data)}")
                return
            
            nodes_list = nodes_data.get("nodes", [])
            
            async with AsyncSessionLocal() as db:
                for n in nodes_list:
                    node_id = str(n.get("nodeId"))
                    if not node_id:
                        continue
                    
                    # Update or Create Node
                    await self._sync_node_info(db, n)
                    
                    # 2. Ping Check (only if connected)
                    if n.get("connected"):
                        await self._ping_node(db, node_id)
                    else:
                        # Mark offline metrics
                        await self._record_metric(db, node_id, rtt=None, success=False)
 
        except Exception as e:
            logger.error(f"Check nodes error: {e}")
 
    async def _sync_node_info(self, db: AsyncSession, n: Dict):
        node_id = str(n.get("nodeId"))
        result = await db.execute(select(Node).filter(Node.id == node_id))
        existing = result.scalars().first()
        
        new_status = NodeStatus.ONLINE if n.get("connected") else NodeStatus.OFFLINE
 
        if existing:
            existing.status = new_status
            existing.last_heartbeat = datetime.now()
            if n.get("displayName"):
                existing.name = n.get("displayName")
            if n.get("version"):
                existing.version = n.get("version")
        else:
            new_node = Node(
                id=node_id,
                name=n.get("displayName", f"Node-{node_id[:8]}"),
                platform=n.get("platform", "unknown"),
                status=new_status,
                version=n.get("version"),
                ip_address=n.get("remoteIp"),
                last_heartbeat=datetime.now()
            )
            db.add(new_node)
        
        await db.commit()
 
    async def _ping_node(self, db: AsyncSession, node_id: str):
        """Send a lightweight command to measure RTT"""
        start_ts = time.time()
        
        try:
            try:
                # Use client.request for invocation
                await self.client.request("node.invoke", {
                    "nodeId": node_id,
                    "command": "canvas.info",
                    "params": {},
                    "timeoutMs": 3000,
                    "idempotencyKey": f"ping-{node_id}-{int(start_ts * 1000)}"
                }, timeout=5.0)
                
                rtt = (time.time() - start_ts) * 1000
                await self._record_metric(db, node_id, rtt, True)
            except Exception as e:
                # If command fails but request returns (e.g. not supported), RTT is still valid
                rtt = (time.time() - start_ts) * 1000
                if "not allowed" in str(e).lower() or "command not supported" in str(e).lower():
                    await self._record_metric(db, node_id, None, True)
                else:
                    await self._record_metric(db, node_id, rtt, False)
            
        except Exception as e:
            logger.debug(f"Ping failed for {node_id}: {e}")
            await self._record_metric(db, node_id, None, False)
 
    async def _record_metric(self, db: AsyncSession, node_id: str, rtt: Optional[float], success: bool):
        # Update Stats Cache
        stats = self.stats.setdefault(node_id, {"pings": 0, "failures": 0, "total_rtt": 0.0})
        stats["pings"] += 1
        if not success:
            stats["failures"] += 1
        elif rtt is not None:
            stats["total_rtt"] += rtt
            
        # Calculate Packet Loss
        loss_rate = (stats["failures"] / stats["pings"]) * 100 if stats["pings"] > 0 else 0
        
        # Calculate Average RTT (for successful pings only)
        successful_pings = stats["pings"] - stats["failures"]
        avg_rtt = stats["total_rtt"] / successful_pings if successful_pings > 0 else None
        
        # Create Metric
        metric = NodeMetricCreate(
            cpu_usage=0,
            memory_usage=0,
            disk_usage=0,
            network_in=0,
            network_out=0,
            latency=avg_rtt if rtt is not None else None,
            packet_loss=loss_rate
        )
        
        # logger.debug(f"Node {node_id}: RTT={rtt:.2f}ms, Loss={loss_rate:.1f}%")
        await node_manager.heartbeat(db, node_id, metric)
 
 
node_monitor = NodeMonitor.get_instance()
