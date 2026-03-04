"""
OpenClaw Task Sharding & Dispatch

负责将任务拆解并根据策略分发到不同的节点。
支持 Broadcast, Round-Robin, Targeted 等策略。
"""

import asyncio
import logging
from enum import Enum
from typing import List, Dict, Any, Optional
from app.models.node import Node
from app.services.openclaw.gateway.dispatch import DispatchService
from app.core.logger import logger

class ShardingStrategy(str, Enum):
    BROADCAST = "broadcast"       # Send same task to all selected nodes
    ROUND_ROBIN = "round_robin"   # Distribute subtasks to nodes in RR fashion
    TARGETED = "targeted"         # Send specific task to specific node (handled by caller usually, but here for completeness)
    RANDOM = "random"             # Randomly pick a node for the task

class TaskSharder:
    
    def __init__(self, dispatch_service: DispatchService):
        self.dispatch_service = dispatch_service

    async def shard_and_dispatch(
        self, 
        task_id: str,
        payloads: List[Dict[str, Any]] | Dict[str, Any], 
        nodes: List[Node], 
        strategy: ShardingStrategy = ShardingStrategy.ROUND_ROBIN
    ) -> Dict[str, Any]:
        """
        分发任务或子任务列表到指定节点集。
        
        Args:
            task_id: 主任务ID
            payloads: 单个任务载荷(Dict) 或 子任务列表(List[Dict])
            nodes: 可用节点列表
            strategy: 分发策略
            
        Returns:
            Dict containing results of dispatch (success/fail counts, details)
        """
        if not nodes:
            logger.warning(f"No nodes available for task {task_id}")
            return {"status": "failed", "reason": "no_nodes"}

        results = []
        
        # Normalize payloads to list if it's a single dict but strategy implies distribution?
        # If strategy is BROADCAST, payload should be single dict (or list sent to all).
        # If strategy is ROUND_ROBIN, payload should be list of subtasks ideally.
        
        if strategy == ShardingStrategy.BROADCAST:
            if isinstance(payloads, list):
                # Broadcast sequence of tasks to all nodes? Or just one?
                # Usually broadcast means "Run X on all nodes".
                # If payloads is a list, maybe "Run X1, X2... on all nodes".
                pass
            else:
                payloads = [payloads] # Wrap single task
            
            # For each payload, send to ALL nodes
            tasks = []
            for payload in payloads:
                for node in nodes:
                    tasks.append(self.dispatch_service.dispatch_to_gateway(payload, node.id, task_id))
            
            # Execute concurrently
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            results.extend(batch_results)

        elif strategy == ShardingStrategy.TARGETED:
            # Expect payloads to be a dict mapping node_id -> payload
            # OR a list of payloads where each payload contains 'target_node_id'
            # OR provided 'nodes' list aligns with 'payloads' list 1-to-1?
            # Let's support: payloads is a list of dicts, and we expect len(payloads) == len(nodes)
            # This allows "LLM parsed multiple subtasks... assign to nodes list".
            
            if not isinstance(payloads, list):
                logger.error("Targeted strategy requires a list of payloads matching nodes")
                return {"status": "failed", "reason": "invalid_payloads"}
                
            if len(payloads) != len(nodes):
                # Try to map as many as possible? Or fail?
                # If we have more tasks than nodes, maybe round robin the rest?
                # But if it's "Targeted", it usually implies specific assignment.
                # However, the prompt says: "LLM parses multiple subtasks... according to node_ids list... dispatch concurrently".
                # This sounds like: Task 1 -> Node A, Task 2 -> Node B.
                # If tasks > nodes, maybe Task 3 -> Node A again? (That's Round Robin)
                # If "Targeted" means "I have specific node for each task", then payload should have node info.
                # Let's assume for this strategy, we map payload[i] -> nodes[i].
                # If len mismatch, we log warning and stop or loop nodes?
                # Let's loop nodes if tasks > nodes (like Round Robin but strictly ordered start?)
                pass
            
            # Actually, "Targeted" usually means the assignment is already decided.
            # If the LLM decided "Task A on Node 1", then `nodes` argument might be redundant or just for validation.
            # Let's implement: Iterate payloads. If payload has 'node_id', use it. 
            # Else, use nodes[i % len(nodes)] (Round Robin fallback).
            
            tasks = []
            num_nodes = len(nodes)
            for i, payload in enumerate(payloads):
                target_node_id = payload.get("target_node_id") or payload.get("nodeId")
                
                if target_node_id:
                    # Validate if this node is in our available nodes list?
                    # Maybe not strictly required if we trust the source, but safer.
                    pass
                else:
                    # Fallback to round robin from provided list
                    if num_nodes > 0:
                        target_node_id = nodes[i % num_nodes].id
                    else:
                         # No nodes to assign
                         failures.append(f"No node for task {i}")
                         continue

                tasks.append(self.dispatch_service.dispatch_to_gateway(payload, target_node_id, task_id))
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            results.extend(batch_results)

        elif strategy == ShardingStrategy.ROUND_ROBIN:
            if not isinstance(payloads, list):
                payloads = [payloads]
            
            # Distribute payloads across nodes
            tasks = []
            num_nodes = len(nodes)
            if num_nodes == 0:
                logger.error("No nodes for Round Robin dispatch")
                return {"status": "failed", "reason": "no_nodes"}

            for i, payload in enumerate(payloads):
                node = nodes[i % num_nodes]
                tasks.append(self.dispatch_service.dispatch_to_gateway(payload, node.id, task_id))
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            results.extend(batch_results)

        elif strategy == ShardingStrategy.RANDOM:
            import random
            if not isinstance(payloads, list):
                payloads = [payloads]
                
            tasks = []
            for payload in payloads:
                node = random.choice(nodes)
                tasks.append(self.dispatch_service.dispatch_to_gateway(payload, node.id, task_id))
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            results.extend(batch_results)
            
        # Process results
        success_count = 0
        failures = []
        for res in results:
            if isinstance(res, Exception):
                failures.append(str(res))
            elif isinstance(res, dict) and res.get("error"):
                 failures.append(res.get("error"))
            else:
                success_count += 1
                
        return {
            "status": "partial_success" if failures and success_count > 0 else ("success" if not failures else "failed"),
            "total": len(results),
            "success": success_count,
            "failures": failures
        }
