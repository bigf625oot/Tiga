"""
应用场景：
    可靠的任务下发机制。
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

from app.services.openclaw.node.discovery import NodeDiscoveryService
from app.services.openclaw.common.errors import DispatchErrorType, DispatchException, DispatchPhase
from app.models.openclaw_task import OpenClawTask
from app.db.session import AsyncSessionLocal
from app.core.logger import logger
from app.models.node import Node
from app.services.openclaw.node.selector import BaseSelector, TagSelector, LeastLoadSelector, NodeSelectionError, MetricsClient
from app.services.openclaw.task.session import task_session_manager
from app.services.openclaw.gateway.routing_lock import lock_routing_payload, verify_routing_payload

import time
from app.services.openclaw.observability.dispatch_metrics import DispatchMetrics

class MonitorMetricsAdapter:
    """适配节点监控统计信息到指标客户端协议"""
    def get_load(self, node: Node) -> float:
        from app.services.openclaw.node.monitor import node_monitor
        stats = node_monitor.stats.get(node.id, {})
        pings = stats.get("pings", 0)
        if pings > 0:
            return stats.get("total_rtt", 0) / pings
        return 0.0

class DispatchService:
    """
    使用 WebSocket 的可靠分发服务。
    """
    
    SELECTOR_POLICY = "least_load"  # 可配置: 'tag' 或 'least_load'

    def __init__(self, selector: Optional[BaseSelector] = None):
        if selector:
            self.selector = selector
        else:
            if self.SELECTOR_POLICY == "tag":
                self.selector = TagSelector(tags={})
            else:
                self.selector = LeastLoadSelector(metrics_client=MonitorMetricsAdapter())

    async def dispatch(self, task_payload: Dict[str, Any], task_id: str, active_nodes: List[Node]) -> Dict[str, Any]:
        """
        从 active_nodes 中选择合适的节点下发任务。
        返回包含 'node_id' 和网关返回结果的字典。
        """
        if not self.selector:
             raise DispatchException(DispatchErrorType.UNKNOWN, "未配置节点选择器")

        session_id = task_payload.get("session_id")
        node = None

        try:
            # 1. 检查会话亲和性
            if session_id:
                affinity_node_id = task_session_manager.get_affinity_node(session_id)
                if affinity_node_id:
                    affinity_node = next((n for n in active_nodes if n.id == affinity_node_id), None)
                    if affinity_node:
                        node = affinity_node
                        logger.info(f"[分发] 使用亲和性节点 {node.id} 处理会话 {session_id}")
                    else:
                        logger.warning(f"[分发] 亲和性节点 {affinity_node_id} 不可用于会话 {session_id}。触发重新选择。")
                        new_node_id = await task_session_manager.reselect_affinity_node(session_id, affinity_node_id, active_nodes)
                        if new_node_id:
                             node = next((n for n in active_nodes if n.id == new_node_id), None)
                             
            # 2. 常规节点选择
            if not node:
                node = self.selector.select(active_nodes)
            
            if not node:
                 msg = "未找到合适的节点进行分发"
                 logger.error(f"[分发] {msg}")
                 DispatchMetrics.record_dispatch("failure")
                 DispatchMetrics.record_fail_reason("no_node_selected")
                 raise DispatchException(DispatchErrorType.NODE_OFFLINE, msg) 
            
            # 3. 注册新会话
            if session_id:
                meta = {
                    "version": node.version,
                    "location": node.config.get("location") if node.config else None
                }
                task_session_manager.register_session(session_id, node.id, meta)

            gateway_result = await self.dispatch_to_gateway(task_payload, node.id, task_id)
            
            if isinstance(gateway_result, dict):
                gateway_result["_dispatched_node_id"] = node.id
            
            return gateway_result
            
        except NodeSelectionError as e:
             logger.error(f"节点选择错误: {e}")
             raise DispatchException(DispatchErrorType.UNKNOWN, f"节点选择失败: {e}")

    async def dispatch_to_gateway(self, task_payload: Dict[str, Any], node_id: str, task_id: str) -> Dict[str, Any]:
        """
        可靠下发任务到网关 (仅 WebSocket)
        1. 检查节点在线状态
        2. 尝试 WebSocket 下发（3s 超时）
        3. 异常捕获
        """
        start_ts = time.time()
        logger.info(f"开始分发任务到网关 (仅 WS): task_id={task_id}, node={node_id}")
        
        try:
            async with AsyncSessionLocal() as db:
                # 1. 节点状态检查
                try:
                    node_status = await NodeDiscoveryService.get_node_status(node_id, db)
                    status = node_status.get("status")
                    is_local_gateway = (node_id == "gateway")
                    
                    if status == "offline" or (status == "unknown" and not is_local_gateway):
                        logger.error(f"节点状态检查失败: node_id={node_id}, status={status}")
                        raise DispatchException(DispatchErrorType.NODE_OFFLINE, f"节点 {node_id} 离线")
                except DispatchException:
                    raise
                except Exception as e:
                    logger.warning(f"节点检查警告: {e}")
            
            # 2. WebSocket 尝试
            try:
                res = await self._dispatch_ws(task_payload, task_id, node_id)
                DispatchMetrics.record_dispatch("success")
                return res
            except Exception as ws_e:
                logger.error(f"WebSocket 分发失败: {ws_e}")
                if isinstance(ws_e, DispatchException) and ws_e.error_type in (
                    DispatchErrorType.ROUTING_MISSING,
                    DispatchErrorType.ROUTING_INVALID,
                    DispatchErrorType.ROUTING_FORBIDDEN,
                ):
                    DispatchMetrics.record_dispatch("failure")
                    DispatchMetrics.record_fail_reason(ws_e.error_code)
                    raise ws_e
                
                async with AsyncSessionLocal() as db:
                    phase = DispatchPhase.WS_SEND
                    err_type = DispatchErrorType.UNKNOWN
                    if isinstance(ws_e, asyncio.TimeoutError):
                        err_type = DispatchErrorType.WS_TIMEOUT
                        phase = DispatchPhase.WS_ACK
                    elif "not connected" in str(ws_e).lower():
                        err_type = DispatchErrorType.WS_NOT_CONNECTED
                    
                    logger.error(f"分发失败: {err_type} - {ws_e}")
                    
                DispatchMetrics.record_dispatch("failure")
                raise DispatchException(DispatchErrorType.UNKNOWN, f"WebSocket 分发失败: {ws_e}")

        finally:
            DispatchMetrics.observe_latency(start_ts)

    async def _dispatch_ws(self, payload: Dict[str, Any], task_id: str, node_id: str) -> Dict[str, Any]:
        """WebSocket 下发逻辑"""
        from app.services.openclaw.node.monitor import node_monitor
        if not node_monitor.running or not node_monitor.client.is_connected:
             raise DispatchException(DispatchErrorType.WS_NOT_CONNECTED, "WebSocket 未连接")

        try:
            locked_payload = lock_routing_payload(payload, node_id, task_id).payload
            verify_routing_payload(locked_payload, expected_node_id=node_id)
            ws_res = await asyncio.wait_for(
                node_monitor.client.request("cron.add", locked_payload, timeout=3.0),
                timeout=3.0
            )
            
            if isinstance(ws_res, dict):
                return ws_res
            else:
                raise Exception(f"无效的 WS 响应: {ws_res}")
                
        except asyncio.TimeoutError:
            raise DispatchException(DispatchErrorType.WS_TIMEOUT, "WebSocket 请求超时")
        except Exception as e:
            raise e

    async def _log_fail(self, db: AsyncSession, task_id: str, node_id: str, phase: DispatchPhase, 
                       err_type: DispatchErrorType, message: str):
        """记录失败日志"""
        try:
            logger.error(f"[失败日志] 任务={task_id} 节点={node_id} 阶段={phase.value} 类型={err_type.value} 消息={message}")
            
            from app.crud.crud_openclaw_task import OpenClawTaskCRUD
            await OpenClawTaskCRUD.update_task_status_with_optimistic_lock(
                db, task_id, "PENDING", "FAILED", 
                json.dumps({"phase": phase.value, "type": err_type.value, "msg": message})
            )
        except Exception as e:
            logger.error(f"记录分发失败日志失败: {e}")
