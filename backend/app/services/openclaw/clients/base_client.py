"""
WebSocket 客户端基础抽象类
封装了通用的连接管理、消息收发、重连机制
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional, Awaitable

import websockets
from websockets.exceptions import ConnectionClosed

logger = logging.getLogger("openclaw.ws_base")


class ConnectionError(Exception):
    """连接相关错误"""

class RequestError(Exception):
    """请求相关错误"""

class TimeoutError(Exception):
    """超时错误"""


class WebSocketBaseClient(ABC):
    """
    WebSocket 客户端基类
    提供通用的连接管理、消息收发、请求-响应、重连机制
    """
    
    def __init__(
        self,
        *,
        client_id: str,
        ws_url: str,
        auto_reconnect: bool = True,
        reconnect_delay: float = 3.0,
        max_reconnect_attempts: int = 0,
        ping_interval: float = 20.0,
        ping_timeout: float = 20.0,
        message_max_size: int = 16 * 1024 * 1024,
    ):
        self.client_id = client_id
        self.ws_url = ws_url
        self.auto_reconnect = auto_reconnect
        self.reconnect_delay = reconnect_delay
        self.max_reconnect_attempts = max_reconnect_attempts
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        self.message_max_size = message_max_size
        
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._running = False
        self._reconnect_count = 0
        self._pending: Dict[str, asyncio.Future] = {}
        self._recv_task: Optional[asyncio.Task] = None
        self._reconnect_task: Optional[asyncio.Task] = None
        self._manual_close = False
        self._last_disconnect_context: str = "unknown"
        
        # 外部回调
        self.on_message: Optional[Callable[[Dict], Awaitable[None]]] = None
        self.on_connect: Optional[Callable[[], Awaitable[None]]] = None
        self.on_disconnect: Optional[Callable[[], Awaitable[None]]] = None
    
    @property
    def is_connected(self) -> bool:
        return self._running and self._ws is not None

    @property
    def last_disconnect_context(self) -> str:
        return self._last_disconnect_context
    
    async def connect(self) -> bool:
        """建立连接（子类可重写添加认证逻辑）"""
        self._manual_close = False
        if self.is_connected:
            return True
            
        logger.info(f"[{self.client_id}] 正在连接: {self.ws_url}")
        
        try:
            self._ws = await websockets.connect(
                self.ws_url,
                open_timeout=10,
                ping_interval=self.ping_interval,
                ping_timeout=self.ping_timeout,
                max_size=self.message_max_size,
                additional_headers=await self._get_headers(),
            )
        except Exception as e:
            logger.error(f"[{self.client_id}] 连接失败: {e}")
            return False
        
        self._running = True
        self._reconnect_count = 0
        self._last_disconnect_context = "connected"
        self._recv_task = asyncio.create_task(
            self._recv_loop(), name=f"ws-recv-{self.client_id}"
        )
        try:
            await self._after_connect()  # 子类实现认证等后置逻辑
        except Exception as e:
            logger.error(f"[{self.client_id}] 连接后置处理失败: {e}")
            self._running = False
            if self._recv_task and not self._recv_task.done():
                self._recv_task.cancel()
            self._recv_task = None
            self._cancel_all_pending("连接后置处理失败")
            await self._close_ws()
            return False
        
        logger.info(f"[{self.client_id}] 连接成功")
        
        if self.on_connect:
            await self._safe_callback(self.on_connect)
        
        return True
    
    async def disconnect(self, reason: str = "manual") -> None:
        """断开连接"""
        self._manual_close = True
        self._last_disconnect_context = f"local_close:{reason}"
        logger.info(f"[{self.client_id}] 主动关闭连接: reason={reason}")
        self._running = False
        if self._recv_task and not self._recv_task.done():
            self._recv_task.cancel()
        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()
        self._cancel_all_pending("连接已断开")
        await self._close_ws()
        
        if self.on_disconnect:
            await self._safe_callback(self.on_disconnect)

    async def close(self, reason: str = "manual") -> None:
        await self.disconnect(reason=reason)
    
    async def request(self, method: str, params: Dict[str, Any], timeout: float = 10.0) -> Any:
        """发送请求并等待响应"""
        if not self.is_connected:
            raise ConnectionError("未连接")
        
        req_id = str(uuid.uuid4())
        frame = {
            "type": "req",
            "id": req_id,
            "method": method,
            "params": params
        }
        
        fut = asyncio.get_event_loop().create_future()
        self._pending[req_id] = fut
        
        await self._ws.send(json.dumps(frame))
        
        try:
            return await asyncio.wait_for(fut, timeout=timeout)
        except asyncio.TimeoutError:
            self._pending.pop(req_id, None)
            raise TimeoutError(f"请求超时: {method}")
    
    # ───────────── 子类可重写的方法 ─────────────
    
    async def _get_headers(self) -> Dict[str, str]:
        """获取连接头信息（子类可重写）"""
        return {"User-Agent": f"{self.client_id}/1.0.0"}
    
    async def _after_connect(self) -> None:
        """连接后的处理（子类实现认证逻辑）"""
        pass
    
    async def _handle_message(self, data: Dict) -> bool:
        """
        处理消息
        返回 True 表示已处理，False 表示需要继续传递给 on_message
        """
        msg_type = data.get("type")
        msg_id = data.get("id")
        
        # 处理响应
        if msg_type == "res" and msg_id in self._pending:
            fut = self._pending.pop(msg_id)
            if not fut.done():
                if data.get("ok"):
                    fut.set_result(data.get("payload"))
                else:
                    fut.set_exception(RequestError(str(data.get("error"))))
            return True
        
        return False
    
    # ───────────── 内部方法 ─────────────
    
    async def _recv_loop(self) -> None:
        """接收循环"""
        try:
            async for raw in self._ws:
                await self._dispatch(raw)
        except ConnectionClosed as e:
            code = getattr(e, "code", None)
            reason = getattr(e, "reason", "") or ""
            if code == 1008:
                category = "server_policy_reject_or_auth_failed"
            else:
                category = "peer_or_network_close"
            self._last_disconnect_context = f"{category}:code={code},reason={reason}"
            logger.info(
                f"[{self.client_id}] 连接断开: category={category}, code={code}, reason={reason}"
            )
        except Exception as e:
            self._last_disconnect_context = f"recv_exception:{type(e).__name__}"
            logger.error(f"[{self.client_id}] 接收错误: {e}")
        finally:
            should_reconnect = (not self._manual_close) and self.auto_reconnect
            self._running = False
            self._cancel_all_pending("连接断开")
            if should_reconnect:
                self._reconnect_task = asyncio.create_task(self._reconnect_loop())
    
    async def _dispatch(self, raw: str) -> None:
        """分发消息"""
        try:
            data = json.loads(raw)
            
            # 先让子类处理
            if await self._handle_message(data):
                return
            
            # 子类没处理，交给回调
            if self.on_message:
                await self._safe_callback(self.on_message, data)
                
        except Exception as e:
            logger.error(f"[{self.client_id}] 消息处理错误: {e}")
    
    async def _reconnect_loop(self) -> None:
        """重连循环"""
        if self.max_reconnect_attempts > 0 and self._reconnect_count >= self.max_reconnect_attempts:
            logger.error(f"[{self.client_id}] 达到最大重连次数")
            return
        
        self._reconnect_count += 1
        delay = min(self.reconnect_delay * (2 ** (self._reconnect_count - 1)), 60)
        logger.info(f"[{self.client_id}] 将在 {delay}s 后第 {self._reconnect_count} 次重连")
        
        await asyncio.sleep(delay)
        await self.connect()
    
    async def _close_ws(self) -> None:
        """关闭连接"""
        if self._ws:
            try:
                await self._ws.close()
            except Exception:
                pass
            self._ws = None
    
    def _cancel_all_pending(self, reason: str) -> None:
        """取消所有待处理请求"""
        if not self._pending:
            return
        exc = ConnectionError(reason)
        for fut in list(self._pending.values()):
            if not fut.done():
                fut.set_exception(exc)
        self._pending.clear()
    
    async def _safe_callback(self, callback: Callable, *args, **kwargs) -> None:
        """安全执行回调"""
        try:
            await callback(*args, **kwargs)
        except Exception as e:
            logger.error(f"[{self.client_id}] 回调执行失败: {e}")
