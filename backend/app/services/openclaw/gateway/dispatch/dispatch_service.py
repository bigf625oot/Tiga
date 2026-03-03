"""
应用场景：
    可靠的任务下发机制（WebSocket -> HTTP 降级）。
    确保关键任务能够送达网关或节点。

核心功能：
    - 节点状态检查（Redis/DB）
    - 带超时的 WebSocket 下发
    - HTTP 降级下发
    - 失败日志记录与指标监控

__author__ = "xucao"
Created: 2025-03
"""

import asyncio
import json
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert

from app.services.openclaw.node.discovery.node_discovery_service import NodeDiscoveryService
from app.services.openclaw.utils.dispatch.exception import DispatchErrorType, DispatchException, DispatchPhase
from app.services.openclaw.clients.http.client import OpenClawHttpClient
from app.models.openclaw_task import OpenClawTask
from app.db.session import AsyncSessionLocal
from app.core.logger import logger
from app.models.node import Node
from app.services.openclaw.node.selector import BaseSelector, TagSelector, LeastLoadSelector, NodeSelectionError, MetricsClient
from app.services.openclaw.task.session.session_manager import task_session_manager

import time
from app.services.openclaw.utils.metrics import DispatchMetrics

class MonitorMetricsAdapter:
    """Adapts node_monitor stats to MetricsClient protocol."""
    def get_load(self, node: Node) -> float:
        # Use average RTT as a proxy for load if available, else 0
        from app.services.openclaw.node.monitor.node_monitor_service import node_monitor
        stats = node_monitor.stats.get(node.id, {})
        pings = stats.get("pings", 0)
        if pings > 0:
            return stats.get("total_rtt", 0) / pings
        return 0.0

class DispatchService:
    """双通道（WebSocket -> HTTP）可靠下发服务"""
    
    SELECTOR_POLICY = "least_load"  # Configurable: 'tag' or 'least_load'

    def __init__(self, http_client: OpenClawHttpClient, selector: Optional[BaseSelector] = None):
        self.http_client = http_client
        
        # Initialize selector based on policy if not provided
        if selector:
            self.selector = selector
        else:
            if self.SELECTOR_POLICY == "tag":
                # Default tag selector - empty tags matches all (as superset of empty is everything? No, empty dict is subset of any dict)
                # If we want to match all, tags={} is correct.
                self.selector = TagSelector(tags={})
            else:
                # Default to LeastLoadSelector
                self.selector = LeastLoadSelector(metrics_client=MonitorMetricsAdapter())

    async def dispatch(self, task_payload: Dict[str, Any], task_id: str, active_nodes: List[Node]) -> Dict[str, Any]:
        """
        Dispatch task to a suitable node selected from active_nodes.
        Returns a dict including 'node_id' and 'result' from gateway.
        """
        if not self.selector:
             raise DispatchException(DispatchErrorType.UNKNOWN, "No selector configured")

        session_id = task_payload.get("session_id")
        node = None

        try:
            # 1. Check Session Affinity
            if session_id:
                affinity_node_id = task_session_manager.get_affinity_node(session_id)
                if affinity_node_id:
                    # Verify if affinity node is in active_nodes
                    affinity_node = next((n for n in active_nodes if n.id == affinity_node_id), None)
                    if affinity_node:
                        node = affinity_node
                        logger.info(f"[Dispatch] Using affinity node {node.id} for session {session_id}")
                    else:
                        # Affinity node not active, trigger re-selection
                        logger.warning(f"[Dispatch] Affinity node {affinity_node_id} unavailable for session {session_id}. Triggering re-selection.")
                        new_node_id = await task_session_manager.reselect_affinity_node(session_id, affinity_node_id, active_nodes)
                        if new_node_id:
                             node = next((n for n in active_nodes if n.id == new_node_id), None)
                             
            # 2. Regular Selection if no node selected yet
            if not node:
                # Select node
                node = self.selector.select(active_nodes)
            
            if not node:
                 # Log error and return 503 equivalent (DispatchException)
                 msg = "No suitable node found for dispatch"
                 logger.error(f"[Dispatch] {msg}")
                 # Record failure metric?
                 DispatchMetrics.record_dispatch("failure")
                 DispatchMetrics.record_fail_reason("no_node_selected")
                 raise DispatchException(DispatchErrorType.NODE_OFFLINE, msg) 
            
            # 3. Register Session if new session
            if session_id:
                # Extract metadata for session (e.g. version, location) from node
                # Assuming we have access to node details
                meta = {
                    "version": node.version,
                    "location": node.config.get("location") if node.config else None
                }
                task_session_manager.register_session(session_id, node.id, meta)

            # Call dispatch_to_gateway
            gateway_result = await self.dispatch_to_gateway(task_payload, node.id, task_id)
            
            # Inject node_id into result so caller knows where it went
            if isinstance(gateway_result, dict):
                gateway_result["_dispatched_node_id"] = node.id
            
            return gateway_result
            
        except NodeSelectionError as e:
             logger.error(f"Node selection error: {e}")
             raise DispatchException(DispatchErrorType.UNKNOWN, f"Node selection failed: {e}")

    async def dispatch_to_gateway(self, task_payload: Dict[str, Any], node_id: str, task_id: str) -> Dict[str, Any]:
        """
        可靠下发任务到网关
        1. 检查节点在线状态
        2. 尝试 WebSocket 下发（3s 超时）
        3. 回退 HTTP 下发（3s 超时）
        4. 异常捕获与重试逻辑
        """
        start_ts = time.time()
        logger.info(f"开始分发任务到网关: task_id={task_id}, node={node_id}")
        
        try:
            async with AsyncSessionLocal() as db:
                # 1. 节点状态检查
                logger.debug(f"检查节点状态: node_id={node_id}")
                try:
                    node_status = await NodeDiscoveryService.get_node_status(node_id, db)
                    status = node_status.get("status")
                    
                    # 特殊处理：如果是分发给 gateway 自身（单机模式），且状态为 unknown（未注册），允许通过
                    is_local_gateway = (node_id == "gateway")
                    
                    if status == "offline" or (status == "unknown" and not is_local_gateway):
                        logger.error(f"节点状态检查失败: node_id={node_id}, status={status}")
                        await self._log_fail(db, task_id, node_id, DispatchPhase.NODE_CHECK, 
                                           DispatchErrorType.NODE_OFFLINE, "Node is offline or status unknown")
                        raise DispatchException(DispatchErrorType.NODE_OFFLINE, f"Node {node_id} is offline")
                    elif is_local_gateway and status == "unknown":
                        logger.info(f"Gateway node status is unknown (likely standalone mode), proceeding assuming online.")

                except DispatchException:
                    raise
                except Exception as e:
                    logger.error(f"Node check failed: {e}\n{traceback.format_exc()}")
                    # 允许继续尝试，可能是 Redis 故障
            
            # 2. WebSocket 尝试
            try:
                logger.info(f"尝试 WebSocket 下发: task_id={task_id}")
                res = await self._dispatch_ws(task_payload, task_id, node_id)
                logger.info(f"WebSocket 下发成功: task_id={task_id}")
                DispatchMetrics.record_dispatch("success")
                return res
            except Exception as ws_e:
                logger.warning(f"WebSocket dispatch failed: {ws_e}, falling back to HTTP\n{traceback.format_exc()}")
                
                # 记录 WS 失败日志
                async with AsyncSessionLocal() as db:
                    phase = DispatchPhase.WS_SEND
                    err_type = DispatchErrorType.UNKNOWN
                    if isinstance(ws_e, asyncio.TimeoutError):
                        err_type = DispatchErrorType.WS_TIMEOUT
                        phase = DispatchPhase.WS_ACK
                    elif "not connected" in str(ws_e).lower():
                        err_type = DispatchErrorType.WS_NOT_CONNECTED
                    
                    await self._log_fail(db, task_id, node_id, phase, err_type, str(ws_e))

                # 3. HTTP 回退尝试
                try:
                    logger.info(f"尝试 HTTP 回退下发: task_id={task_id}")
                    res = await self._dispatch_http(task_payload, task_id, node_id)
                    logger.info(f"HTTP 下发成功: task_id={task_id}")
                    DispatchMetrics.record_dispatch("success")
                    return res
                except Exception as http_e:
                    logger.error(f"HTTP dispatch failed: {http_e}\n{traceback.format_exc()}")
                    
                    # 记录 HTTP 失败日志
                    async with AsyncSessionLocal() as db:
                        phase = DispatchPhase.HTTP_SEND
                        err_type = DispatchErrorType.UNKNOWN
                        if isinstance(http_e, asyncio.TimeoutError):
                            err_type = DispatchErrorType.HTTP_TIMEOUT
                            phase = DispatchPhase.HTTP_RESP
                        elif "4" in str(http_e): 
                            err_type = DispatchErrorType.HTTP_4XX
                        elif "5" in str(http_e):
                            err_type = DispatchErrorType.HTTP_5XX
                        
                        await self._log_fail(db, task_id, node_id, phase, err_type, str(http_e))
                    
                    DispatchMetrics.record_dispatch("failure")
                    DispatchMetrics.record_fail_reason(err_type.value)
                    
                    # 抛出最终异常
                    if isinstance(http_e, DispatchException):
                        raise http_e
                    raise DispatchException(DispatchErrorType.UNKNOWN, f"All dispatch attempts failed: {http_e}")
        finally:
            DispatchMetrics.observe_latency(start_ts)

    async def _dispatch_ws(self, payload: Dict[str, Any], task_id: str, node_id: str) -> Dict[str, Any]:
        """WebSocket 下发逻辑"""
        from app.services.openclaw.node.monitor.node_monitor_service import node_monitor
        if not node_monitor.running or not node_monitor.client.is_connected:
             raise DispatchException(DispatchErrorType.WS_NOT_CONNECTED, "WebSocket not connected")

        try:
            # 设置 3 秒超时
            ws_res = await asyncio.wait_for(
                node_monitor.client.request("cron.add", payload, timeout=3.0),
                timeout=3.0
            )
            
            if isinstance(ws_res, dict):
                return ws_res
            else:
                raise Exception(f"Invalid WS response: {ws_res}")
                
        except asyncio.TimeoutError:
            raise DispatchException(DispatchErrorType.WS_TIMEOUT, "WebSocket request timed out")
        except Exception as e:
            raise e

    async def _dispatch_http(self, payload: Dict[str, Any], task_id: str, node_id: str) -> Dict[str, Any]:
        """HTTP 下发逻辑"""
        try:
            # 使用 HTTP 客户端调用，设置 3 秒超时
            # 注意：这里假设 http_client.invoke 支持 timeout 参数，或者在 client 初始化时设置
            # 如果 client 不支持单次 timeout，需要修改 client 代码
            
            # payload 转换
            http_payload = {
                "action": "add",
                **payload
            }
            
            # 这里模拟 timeout
            res = await asyncio.wait_for(
                self.http_client.invoke("cron", http_payload),
                timeout=3.0
            )
            
            if res.get("error"):
                 status = res.get("status", 500)
                 if 400 <= status < 500:
                     raise DispatchException(DispatchErrorType.HTTP_4XX, res["error"])
                 else:
                     raise DispatchException(DispatchErrorType.HTTP_5XX, res["error"])
            
            return res
            
        except asyncio.TimeoutError:
             raise DispatchException(DispatchErrorType.HTTP_TIMEOUT, "HTTP request timed out")
        except Exception as e:
            raise e

    async def _log_fail(self, db: AsyncSession, task_id: str, node_id: str, phase: DispatchPhase, 
                       err_type: DispatchErrorType, message: str):
        """记录失败日志"""
        try:
            # 假设有一个 task_fail_logs 表
            # await db.execute(insert(TaskFailLog).values(...))
            # 由于没有该表定义，这里仅打印日志，实际应入库
            logger.error(f"[FAIL_LOG] Task={task_id} Node={node_id} Phase={phase.value} Type={err_type.value} Msg={message}")
            
            # 更新任务表中的 error_log
            from app.crud.crud_openclaw_task import OpenClawTaskCRUD
            await OpenClawTaskCRUD.update_task_status_with_optimistic_lock(
                db, task_id, "PENDING", "FAILED", 
                json.dumps({"phase": phase.value, "type": err_type.value, "msg": message})
            )
        except Exception as e:
            logger.error(f"Failed to log dispatch failure: {e}")
