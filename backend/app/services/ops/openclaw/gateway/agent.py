"""
此模块用于管理 Agno 代理 (Agent) 的 WebSocket 连接。
主要功能包括：
1. 身份验证：通过 HMAC-SHA256 签名验证代理的合法性，防止非法接入。
2. 连接管理：维护代理 ID 与 WebSocket 连接的映射关系。
3. 协议处理：实现 oc.agent.v1 协议，处理 JSON-RPC 2.0 消息（执行、查询、取消任务）。
4. 任务模拟：异步处理代理任务请求并推送状态变更事件（开始、完成、失败）。
"""

import asyncio
import hmac
import hashlib
import json
import logging
import time
import random
from typing import Dict
from fastapi import WebSocket, status

from app.core.config import settings

logger = logging.getLogger("openclaw.gateway.agent")

class AgnoConnectionManager:
    """
    管理来自 Agno 代理的 WebSocket 连接。
    协议版本: oc.agent.v1
    """
    def __init__(self):
        # 活跃连接映射：agent_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        # 任务映射：task_id -> agent_id (用于追踪任务所属的代理)
        self.task_agent_map: Dict[str, str] = {}

    async def connect(self, websocket: WebSocket):
        """建立 WebSocket 连接并进行身份验证"""
        await websocket.accept(subprotocol="oc.agent.v1")
        
        try:
            # 身份验证
            agent_id = await self._authenticate(websocket)
            self.active_connections[agent_id] = websocket
            logger.info(f"代理 {agent_id} 已连接。")
            return agent_id
        except Exception as e:
            logger.error(f"身份验证失败: {e}，将关闭连接 code=1008")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            raise

    def disconnect(self, agent_id: str):
        """断开代理连接"""
        if agent_id in self.active_connections:
            del self.active_connections[agent_id]
        logger.info(f"代理 {agent_id} 已断开。")

    async def _authenticate(self, websocket: WebSocket) -> str:
        """
        验证请求头中的 HMAC 签名
        需要字段: x-agno-key, x-agno-signature, x-agno-timestamp, x-agno-nonce
        """
        headers = websocket.headers
        api_key = headers.get("x-agno-key")
        signature = headers.get("x-agno-signature")
        timestamp = headers.get("x-agno-timestamp")
        nonce = headers.get("x-agno-nonce")

        if not all([api_key, signature, timestamp, nonce]):
            raise Exception("缺少身份验证请求头")

        # 验证时间戳（允许 5 分钟偏差，防止重放攻击）
        if abs(time.time() - int(timestamp)) > 300:
            raise Exception("时间戳已过期")

        # 验证签名 (实际生产中应根据 api_key 从数据库获取 secret)
        effective_secret = getattr(settings, "OPENCLAW_AGNO_SECRET", "test-secret")
        
        payload = f"{api_key}{timestamp}{nonce}".encode("utf-8")
        expected_signature = hmac.new(
            effective_secret.encode("utf-8"),
            payload,
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_signature):
             raise Exception("签名无效")

        return api_key # 暂时使用 api_key 作为 agent_id

    async def handle_message(self, agent_id: str, message_data: str):
        """解析并处理收到的 JSON-RPC 消息"""
        try:
            data = json.loads(message_data)
            msg_id = data.get("id")
            method = data.get("method")
            
            if method == "ping":
                await self.send_json(agent_id, {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": "pong"
                })
                return

            if method == "execute":
                await self._handle_execute(agent_id, msg_id, data.get("params"))
            elif method == "query":
                await self._handle_query(agent_id, msg_id, data.get("params"))
            elif method == "cancel":
                await self._handle_cancel(agent_id, msg_id, data.get("params"))
            else:
                await self.send_error(agent_id, msg_id, -32601, "未找到该方法")

        except json.JSONDecodeError:
            pass # 忽略格式错误的 JSON
        except Exception as e:
            logger.error(f"处理来自 {agent_id} 的消息时出错: {e}")

    async def _handle_execute(self, agent_id: str, msg_id: str, params: Dict):
        """处理任务执行请求"""
        task_id = f"task-{int(time.time())}"
        self.task_agent_map[task_id] = agent_id
        
        # 确认收到请求
        await self.send_json(agent_id, {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {"task_id": task_id, "status": "pending"}
        })

        # 启动异步协程模拟任务执行生命周期
        asyncio.create_task(self._simulate_task_execution(agent_id, task_id, params))

    async def _simulate_task_execution(self, agent_id: str, task_id: str, params: Dict):
        """模拟异步任务的执行过程"""
        await asyncio.sleep(1)
        await self.send_event(agent_id, "task_started", {"task_id": task_id, "timestamp": time.time()})
        
        await asyncio.sleep(2)
        
        # 模拟 90% 的成功率
        if random.random() > 0.1:
            await self.send_event(agent_id, "task_completed", {
                "task_id": task_id, 
                "timestamp": time.time(),
                "result": f"在 {params.get('target')} 上执行了 {params.get('task_type')}"
            })
        else:
             await self.send_event(agent_id, "task_failed", {
                "task_id": task_id, 
                "timestamp": time.time(),
                "error": {"code": 500, "message": "模拟执行失败"}
            })

    async def _handle_query(self, agent_id: str, msg_id: str, params: Dict):
        """处理任务状态查询"""
        await self.send_json(agent_id, {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {"status": "running"}
        })

    async def _handle_cancel(self, agent_id: str, msg_id: str, params: Dict):
        """处理任务取消请求"""
        await self.send_json(agent_id, {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {"status": "cancelled"}
        })

    async def send_json(self, agent_id: str, data: Dict):
        """向指定代理发送 JSON 数据"""
        ws = self.active_connections.get(agent_id)
        if ws:
            try:
                await ws.send_json(data)
            except Exception as e:
                logger.error(f"向代理 {agent_id} 发送数据失败: {e}")

    async def send_error(self, agent_id: str, msg_id: str, code: int, message: str):
        """发送 JSON-RPC 错误响应"""
        await self.send_json(agent_id, {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": code, "message": message}
        })

    async def send_event(self, agent_id: str, method: str, params: Dict):
        """发送主动通知事件（通知消息）"""
        await self.send_json(agent_id, {
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        })

# 全局代理连接管理器实例
agent_ws_manager = AgnoConnectionManager()
