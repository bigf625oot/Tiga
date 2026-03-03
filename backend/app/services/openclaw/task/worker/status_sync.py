"""
OpenClaw Task Status Synchronization & Failover

负责监控任务执行状态，处理节点掉线和任务重连。
实现心跳检测和故障转移机制。
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.models.node import Node, NodeStatus
from app.models.openclaw_task import OpenClawTask
from app.services.openclaw.gateway.dispatch.dispatch_service import DispatchService
from app.core.logger import logger

class TaskStatusSync:
    """
    后台任务，用于同步节点状态和处理任务故障转移。
    """
    
    def __init__(self, dispatch_service: DispatchService):
        self.dispatch_service = dispatch_service
        self.running = False
        
        # Configuration
        self.heartbeat_threshold = timedelta(seconds=30) # Node considered offline if no heartbeat for 30s
        self.sync_interval = 10 # Check every 10 seconds

    async def start(self):
        if self.running:
            return
        self.running = True
        logger.info("Starting TaskStatusSync service...")
        asyncio.create_task(self._run_loop())

    async def stop(self):
        self.running = False
        logger.info("Stopping TaskStatusSync service...")

    async def _run_loop(self):
        while self.running:
            try:
                async with AsyncSessionLocal() as db:
                    # 1. Detect dead nodes
                    dead_nodes = await self._detect_dead_nodes(db)
                    
                    # 2. Handle failover for tasks on dead nodes
                    if dead_nodes:
                        await self._handle_failover(db, dead_nodes)
                        
            except Exception as e:
                logger.error(f"Error in TaskStatusSync loop: {e}")
            
            await asyncio.sleep(self.sync_interval)

    async def _detect_dead_nodes(self, db: AsyncSession) -> List[Node]:
        """
        Identify nodes that have missed heartbeats.
        Update their status to OFFLINE.
        """
        threshold_time = datetime.now() - self.heartbeat_threshold
        
        # Find ONLINE nodes with last_heartbeat < threshold
        query = select(Node).filter(
            Node.status == NodeStatus.ONLINE,
            (Node.last_heartbeat < threshold_time) | (Node.last_heartbeat.is_(None))
        )
        result = await db.execute(query)
        dead_nodes = result.scalars().all()
        
        for node in dead_nodes:
            logger.warning(f"Node {node.id} ({node.name}) missed heartbeat. Marking OFFLINE.")
            node.status = NodeStatus.OFFLINE
            # Optionally update 'updated_at'
            
        if dead_nodes:
            await db.commit()
            
        return dead_nodes

    async def _handle_failover(self, db: AsyncSession, dead_nodes: List[Node]):
        """
        Find pending/dispatched tasks for dead nodes and re-queue/re-dispatch them.
        """
        dead_node_ids = [n.id for n in dead_nodes]
        
        # Find tasks that are DISPATCHED to these nodes
        # Assuming 'DISPATCHED' means assigned but not yet finished.
        # If task is COMPLETED or FAILED, we don't need to do anything.
        query = select(OpenClawTask).filter(
            OpenClawTask.status == "DISPATCHED",
            OpenClawTask.target_node_id.in_(dead_node_ids)
        )
        result = await db.execute(query)
        tasks = result.scalars().all()
        
        for task in tasks:
            logger.info(f"Triggering failover for task {task.task_id} (Node {task.target_node_id} dead)")
            
            # Strategy:
            # 1. Mark current task attempt as FAILED (with log)
            # 2. Create a new task (retry) OR reset status to PENDING?
            # If we reset to PENDING, the dispatch loop (if any) might pick it up.
            # But dispatch usually happens at creation time.
            # We need to explicitly re-dispatch.
            
            # Let's reset status to PENDING and clear target_node_id so it can be re-selected
            # But wait, DispatchService usually takes payload. 
            # OpenClawTask stores 'parsed_command' which is the payload.
            
            # Update task record
            task.status = "PENDING"
            task.error_log = (task.error_log or "") + f"\n[Failover] Node {task.target_node_id} offline. Retrying."
            task.target_node_id = None # Clear target so selector can pick new one
            
            # Commit change so state is consistent
            await db.commit()
            
            # Re-dispatch immediately?
            # We need to call dispatch_service.dispatch again.
            # But dispatch requires task_payload, task_id, active_nodes.
            # We need to fetch active nodes.
            
            try:
                # Fetch active nodes
                from app.services.openclaw.node.manager.metadata import node_metadata_manager
                # We can use simple query or metadata manager
                # Let's get all online nodes
                online_nodes_result = await db.execute(select(Node).filter(Node.status == NodeStatus.ONLINE))
                active_nodes = online_nodes_result.scalars().all()
                
                if not active_nodes:
                    logger.error(f"Failover failed for task {task.task_id}: No active nodes available.")
                    task.status = "FAILED"
                    task.error_log += "\n[Failover] No active nodes available."
                    await db.commit()
                    continue

                # Re-dispatch
                try:
                    res = await self.dispatch_service.dispatch(task.parsed_command, task.task_id, active_nodes)
                    
                    # Update task with new node_id if available
                    new_node_id = res.get("_dispatched_node_id") if isinstance(res, dict) else None
                    if new_node_id:
                        task.status = "DISPATCHED"
                        task.target_node_id = new_node_id
                        task.error_log += f"\n[Failover] Successfully re-dispatched to {new_node_id}"
                        await db.commit()
                        logger.info(f"Task {task.task_id} re-dispatched to {new_node_id}")
                    else:
                        logger.warning(f"Task {task.task_id} re-dispatched but node ID missing in result")
                        # We still commit status update if dispatch didn't raise
                        task.status = "DISPATCHED" 
                        await db.commit()
                        
                except Exception as e:
                    logger.error(f"Failover dispatch failed: {e}")
                    task.status = "FAILED"
                    task.error_log += f"\n[Failover] Dispatch failed: {e}"
                    await db.commit()
                    
            except Exception as e:
                logger.error(f"Failover process error: {e}")

# Global instance (to be initialized with dispatch_service)
task_status_sync = None 

def init_task_status_sync(dispatch_service: DispatchService):
    global task_status_sync
    task_status_sync = TaskStatusSync(dispatch_service)
    return task_status_sync
