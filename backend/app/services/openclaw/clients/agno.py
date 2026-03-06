"""
Agno Agent 专用客户端 - 控制面
"""
import time
import uuid
from typing import Dict, Optional
import logging
import hmac
import hashlib
import asyncio
import sys
from urllib.parse import urlparse


# 导入基础客户端 base_client
from app.services.openclaw.clients.base_client import WebSocketBaseClient, TimeoutError

logger = logging.getLogger("openclaw.agno")


class AgnoGatewayClient(WebSocketBaseClient):
    """Agno Agent 客户端（控制面）"""
    
    def __init__(
        self,
        gateway_url: str,
        api_key: str,
        api_secret: str,
        **kwargs
    ):
        parsed = urlparse(gateway_url)
        if parsed.scheme not in ("ws", "wss"):
            raise ValueError("AgnoGatewayClient 仅支持 ws/wss 协议的 gateway_url")

        normalized_gateway_url = gateway_url.rstrip("/")
        ws_url = normalized_gateway_url
        if not ws_url.endswith("/v1/agent"):
            ws_url = f"{ws_url}/v1/agent"
        
        super().__init__(
            client_id="agno-agent",
            ws_url=ws_url,
            ping_interval=None,  # 使用应用层心跳
            **kwargs
        )
        
        self.gateway_url = normalized_gateway_url
        self.api_key = api_key
        self.api_secret = api_secret
        self._active_tasks: Dict[str, asyncio.Future] = {}
    
    async def _get_headers(self) -> Dict[str, str]:
        """生成认证头"""
        nonce = str(uuid.uuid4())
        timestamp = str(int(time.time()))
        
        payload = f"{self.api_key}{timestamp}{nonce}".encode()
        signature = hmac.new(
            self.api_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return {
            "X-Agno-Key": self.api_key,
            "X-Agno-Signature": signature,
            "X-Agno-Timestamp": timestamp,
            "X-Agno-Nonce": nonce,
            "User-Agent": f"Agno-Agent/1.0.0"
        }
    
    async def _after_connect(self) -> None:
        """
        连接后执行握手
        即便使用 Header 认证，OpenClaw Gateway 也要求首个请求必须是 connect
        """
        logger.info(f"[{self.client_id}] 执行握手 (sending connect frame)...")
        try:
            # 构造连接参数
            # 参考 OpenClawWsClient 但简化，因为主要认证已通过 Header 完成
            connect_params = {
                "minProtocol": 3,
                "maxProtocol": 3,
                "client": {
                    "id": "cli",  # 必须是常量 agent
                    "version": "1.0.0",
                    "mode": "backend",
                    "platform": sys.platform,
                    "deviceFamily": "python",
                },
                "role": "operator",
                "auth": {
                    "token": self.api_key # 尝试使用 api_key 作为 token
                }
            }
            
            # 发送 connect 请求
            # 注意：如果服务器发送了 challenge，它会被 _recv_loop 接收并分发
            # 如果我们需要 nonce，应该通过 _handle_message 捕获
            # 这里暂时假设 Header 认证模式下不需要再次签名 nonce
            await self.request("connect", connect_params, timeout=10.0)
            
            logger.info(f"[{self.client_id}] 握手成功")
            
        except Exception as e:
            logger.error(f"[{self.client_id}] 握手失败: {e}")
            raise
    
    async def _handle_message(self, data: Dict) -> bool:
        """处理任务事件"""
        if await super()._handle_message(data):
            return True
        
        method = data.get("method")
        if method in ["task_started", "task_completed", "task_failed"]:
            await self._handle_task_event(data)
            return True
        
        return False
    
    async def _handle_task_event(self, data: Dict):
        """处理任务事件"""
        params = data.get("params", {})
        task_id = params.get("task_id")
        method = data.get("method")
        
        if task_id in self._active_tasks and method in ["task_completed", "task_failed"]:
            fut = self._active_tasks.pop(task_id)
            if not fut.done():
                fut.set_result(data)
    
    async def execute_task(
        self, 
        task_type: str, 
        target: str, 
        payload: Dict = None, 
        timeout: int = 60,
        retry_policy: Dict = None
    ) -> Dict:
        """执行任务并等待结果"""
        # 1. 提交任务
        req_id = str(uuid.uuid4())
        result = await self.request("execute", {
            "task_type": task_type,
            "target": target,
            "payload": payload or {},
            "timeout": timeout,
            "retry_policy": retry_policy,
            "idempotency_key": str(uuid.uuid4())
        }, timeout=10)
        
        task_id = result.get("task_id")
        
        # 2. 等待完成
        fut = asyncio.get_event_loop().create_future()
        self._active_tasks[task_id] = fut
        
        try:
            return await asyncio.wait_for(fut, timeout=timeout)
        except asyncio.TimeoutError:
            self._active_tasks.pop(task_id, None)
            raise TimeoutError(f"任务 {task_id} 执行超时")
