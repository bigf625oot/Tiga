"""
app/core/openclaw_client.py

OpenClawWsClient —— 专用于 Node Monitor 的 WebSocket 客户端（数据面）。
负责与 Gateway 建立长连接，处理节点监控、心跳和实时指令。

协议版本：v3 (Handshake) / v2 (Auth Signature)
Gateway 版本：>= v2026.2.9

认证流程（严格模式）：
1. 连接 WS
2. 接收 connect.challenge (含 nonce)
3. 签名 v2|deviceId|...|nonce (Ed25519)
4. 发送 connect 请求
5. 接收 hello-ok
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from typing import Any, Awaitable, Callable, Dict, Optional
from urllib.parse import urlparse

import websockets
from websockets.exceptions import ConnectionClosed

from app.core.config import settings
from .device_auth import DeviceIdentityManager

logger = logging.getLogger("openclaw.ws")

# ──────────────────────────────────────────────────────────────────────────────
# 协议常量
# ──────────────────────────────────────────────────────────────────────────────
_MIN_PROTOCOL = 3
_MAX_PROTOCOL = 3
_CLIENT_VERSION = "1.0.0"
_DEFAULT_HANDSHAKE_TIMEOUT = 10.0
_DEFAULT_REQUEST_TIMEOUT = 10.0
_DEFAULT_RECONNECT_DELAY = 3.0
_MAX_RECONNECT_ATTEMPTS = 0  # 0 = 无限重连

# 客户端标识
_CLIENT_ID = "cli"       # 必须是枚举值 'cli'
_CLIENT_MODE = "backend" # 必须是枚举值 'cli'/'backend'

# ──────────────────────────────────────────────────────────────────────────────
# 自定义异常
# ──────────────────────────────────────────────────────────────────────────────

class OpenClawError(Exception):
    """OpenClaw 客户端基础异常"""

class OpenClawConnectionError(OpenClawError):
    """连接失败或已断开"""

class OpenClawHandshakeError(OpenClawError):
    """握手/认证失败"""

class OpenClawRequestError(OpenClawError):
    """RPC 请求被 Gateway 拒绝"""
    def __init__(self, message: str, error_payload: Any = None):
        super().__init__(message)
        self.error_payload = error_payload

class OpenClawTimeoutError(OpenClawError):
    """请求超时"""


# ──────────────────────────────────────────────────────────────────────────────
# 主客户端
# ──────────────────────────────────────────────────────────────────────────────

class OpenClawWsClient:
    """
    Openclaw Gateway WebSocket 客户端（异步，operator 角色）。
    仅用于 Node Monitor 和实时指令。
    """

    def __init__(
        self,
        client_id: str = "node-monitor",
        *,
        mode: str = "backend",
        scopes: list[str] | None = None,
        auto_reconnect: bool = True,
        reconnect_delay: float = _DEFAULT_RECONNECT_DELAY,
        max_reconnect_attempts: int = _MAX_RECONNECT_ATTEMPTS,
        key_dir: str | None = None,
    ):
        self.client_id = client_id
        self.mode = mode
        self.scopes = scopes or ["operator.read", "operator.write"]
        self.auto_reconnect = auto_reconnect
        self.reconnect_delay = reconnect_delay
        self.max_reconnect_attempts = max_reconnect_attempts

        self._base_url: str = settings.OPENCLAW_BASE_URL
        self._ws_url: str | None = settings.OPENCLAW_WS_URL
        # 优先使用 OPENCLAW_GATEWAY_TOKEN，如果没有则尝试回退到 OPENCLAW_TOKEN
        self._token: str | None = settings.OPENCLAW_GATEWAY_TOKEN or settings.OPENCLAW_TOKEN

        self._device = DeviceIdentityManager(key_dir=key_dir)

        self._ws: Any = None
        self._running: bool = False
        self._reconnect_count: int = 0

        self._pending: Dict[str, asyncio.Future] = {}
        self._recv_task: asyncio.Task | None = None

        # 外部回调
        self.on_message:    Optional[Callable[[Dict], Awaitable[None]]] = None
        self.on_connect:    Optional[Callable[[], Awaitable[None]]]     = None
        self.on_disconnect: Optional[Callable[[], Awaitable[None]]]     = None

    @property
    def is_connected(self) -> bool:
        return self._running and self._ws is not None

    def _build_ws_url(self) -> str:
        if self._ws_url:
            return self._ws_url
        if not self._base_url:
            raise OpenClawConnectionError("OPENCLAW_BASE_URL 未配置")
        parsed = urlparse(self._base_url)
        scheme = "wss" if parsed.scheme in ("https", "wss") else "ws"
        path = parsed.path.rstrip("/") or ""
        return f"{scheme}://{parsed.netloc}{path}"

    async def connect(self) -> bool:
        if self._running and self._ws:
            return True

        # Pre-check: Verify if any token is available
        has_device_token = self._device.load_device_token() is not None
        if not has_device_token and not self._token:
            logger.error("无法连接 OpenClaw Gateway: 缺少 OPENCLAW_GATEWAY_TOKEN 且无本地 Device Token。请检查 .env 配置。")
            # 不尝试连接，避免刷屏报错
            return False

        ws_url = self._build_ws_url()
        logger.info("WS 连接中: %s (Client: %s)", ws_url, self.client_id)

        try:
            self._ws = await websockets.connect(
                ws_url,
                open_timeout=10,
                ping_interval=20,
                ping_timeout=20,
                max_size=16 * 1024 * 1024,
                additional_headers={
                    "User-Agent": f"Agno-{self.client_id}/{_CLIENT_VERSION}"
                },
            )
        except Exception as exc:
            logger.error(f"WS 连接失败: {exc}")
            return False

        try:
            await self._handshake()
        except Exception as exc:
            logger.error(f"握手失败: {exc}")
            await self._close_ws()
            return False

        self._running = True
        self._reconnect_count = 0
        self._recv_task = asyncio.create_task(
            self._recv_loop(), name=f"openclaw-recv-{self.client_id}"
        )

        logger.info("WS 已连接，设备ID: %s", self._device.device_id)

        if self.on_connect:
            try:
                await self.on_connect()
            except Exception as exc:
                logger.error("on_connect 回调错误: %s", exc)

        return True

    async def disconnect(self) -> None:
        self._running = False
        if self._recv_task and not self._recv_task.done():
            self._recv_task.cancel()
        self._cancel_all_pending("客户端主动断开")
        await self._close_ws()
        if self.on_disconnect:
            try: await self.on_disconnect()
            except: pass

    async def _close_ws(self) -> None:
        if self._ws:
            try: await self._ws.close()
            except: pass
            self._ws = None

    def _cancel_all_pending(self, reason: str) -> None:
        if not self._pending: return
        exc = OpenClawConnectionError(reason)
        for fut in list(self._pending.values()):
            if not fut.done(): fut.set_exception(exc)
        self._pending.clear()

    async def _handshake(self) -> None:
        assert self._ws is not None
        
        # 1. 等待 challenge
        raw = await asyncio.wait_for(self._ws.recv(), timeout=_DEFAULT_HANDSHAKE_TIMEOUT)
        challenge = json.loads(raw)
        nonce = challenge.get("payload", {}).get("nonce")
        if not nonce:
            raise OpenClawHandshakeError("缺少 nonce")

        # 2. 签名
        cached_device_token = self._device.load_device_token()
        # 如果使用 deviceToken，也需要将其包含在签名中（视具体 Gateway 实现而定，此处修正为包含）
        sign_token = self._token if not cached_device_token else cached_device_token

        sig_b64, signed_at = self._device.sign(
            nonce=nonce,
            role="operator",
            scopes=self.scopes,
            token=sign_token,
            client_id=_CLIENT_ID,
            client_mode=self.mode,
        )

        # 3. 发送 connect
        auth_payload = {}
        # 注意：OpenClaw Gateway v2+ 的握手参数中，auth 字段的键名必须是 "token"，即便是 deviceToken 也一样
        if cached_device_token:
            auth_payload["token"] = cached_device_token
        elif self._token:
            auth_payload["token"] = self._token

        connect_frame = {
            "type": "req",
            "id": f"conn-{int(time.time()*1000)}",
            "method": "connect",
            "params": {
                "minProtocol": _MIN_PROTOCOL,
                "maxProtocol": _MAX_PROTOCOL,
                "client": {
                    "id": _CLIENT_ID,
                    "mode": self.mode,
                    "version": _CLIENT_VERSION,
                    "platform": "linux",
                    "deviceFamily": "python",
                },
                "role": "operator",
                "scopes": self.scopes,
                "auth": auth_payload,
                "device": {
                    "id": self._device.device_id,
                    "publicKey": self._device.public_key_b64,
                    "signature": sig_b64,
                    "signedAt": signed_at,
                    "nonce": nonce,
                },
            },
        }
        await self._ws.send(json.dumps(connect_frame))

        # 4. 等待响应
        raw_res = await asyncio.wait_for(self._ws.recv(), timeout=_DEFAULT_HANDSHAKE_TIMEOUT)
        res = json.loads(raw_res)
        
        if not res.get("ok"):
            err = res.get("error", {})
            code = err.get("code")
            msg = err.get("message") or str(err)
            
            # 特殊处理：如果 Token 无效（可能过期），清除本地缓存并报错
            # 下次重连时会自动回退到 Gateway Token 重新登录
            code_str = str(code).upper()
            if "TOKEN" in code_str or "AUTH" in code_str or "SIGNATURE" in code_str or "SCOPE" in code_str:
                logger.warning(f"Device Token 可能失效、签名错误或权限不足 ({code})，清除缓存以重试")
                try:
                    self._device.clear_device_token()
                except Exception as e:
                    logger.error(f"清除 Device Token 失败: {e}")
                
            raise OpenClawHandshakeError(f"握手被拒绝 ({code}): {msg}")

        # 5. 保存新 Token
        auth_info = res.get("payload", {}).get("auth", {})
        if new_token := auth_info.get("deviceToken"):
            self._device.save_device_token(new_token, "operator", self.scopes)

    async def _recv_loop(self) -> None:
        try:
            async for raw in self._ws:
                await self._dispatch(raw)
        except ConnectionClosed:
            logger.info("WS 连接断开")
        except Exception as e:
            logger.error(f"WS 接收循环错误: {e}")
        finally:
            self._running = False
            self._cancel_all_pending("连接断开")
            if self.auto_reconnect:
                asyncio.create_task(self._reconnect_loop())

    async def _reconnect_loop(self) -> None:
        if self.max_reconnect_attempts > 0 and self._reconnect_count >= self.max_reconnect_attempts:
            return
        
        self._reconnect_count += 1
        delay = min(self.reconnect_delay * (2 ** (self._reconnect_count - 1)), 60)
        logger.info(f"将在 {delay}s 后尝试第 {self._reconnect_count} 次重连...")
        await asyncio.sleep(delay)
        await self.connect()

    async def _dispatch(self, raw: str) -> None:
        try:
            data = json.loads(raw)
            msg_type = data.get("type")
            msg_id = data.get("id")

            if msg_type == "res" and msg_id in self._pending:
                fut = self._pending.pop(msg_id)
                if not fut.done():
                    if data.get("ok"):
                        fut.set_result(data.get("payload"))
                    else:
                        fut.set_exception(OpenClawRequestError(str(data.get("error"))))
                return

            if self.on_message:
                await self.on_message(data)

        except Exception as e:
            logger.error(f"消息分发错误: {e}")

    async def request(self, method: str, params: Dict[str, Any], timeout: float = _DEFAULT_REQUEST_TIMEOUT) -> Any:
        if not self.is_connected:
            raise OpenClawConnectionError("未连接")

        req_id = str(uuid.uuid4())
        frame = {"type": "req", "id": req_id, "method": method, "params": params}
        
        fut = asyncio.get_event_loop().create_future()
        self._pending[req_id] = fut
        
        await self._ws.send(json.dumps(frame))
        
        try:
            return await asyncio.wait_for(fut, timeout=timeout)
        except asyncio.TimeoutError:
            self._pending.pop(req_id, None)
            raise OpenClawTimeoutError(f"请求超时: {method}")
