"""
OpenClaw 节点监控客户端 - 数据面
"""
import asyncio
import json
import logging
from typing import Optional, List
from urllib.parse import urlparse

from app.services.openclaw.clients.base_client import WebSocketBaseClient, TimeoutError
from app.services.openclaw.node.auth import DeviceIdentityManager

logger = logging.getLogger("openclaw.monitor")


class OpenClawHandshakeError(Exception):
    """OpenClaw 握手认证异常"""
    pass


class OpenClawWsClient(WebSocketBaseClient):
    """OpenClaw 节点监控客户端（数据面）"""
    
    # 协议常量
    MIN_PROTOCOL = 3
    MAX_PROTOCOL = 3
    CLIENT_VERSION = "1.0.0"
    CLIENT_ID = "cli"
    CLIENT_MODE = "backend"
    
    def __init__(
        self,
        client_id: str = "node-monitor",
        *,
        base_url: str,
        ws_url: Optional[str] = None,
        token: Optional[str] = None,
        scopes: Optional[List[str]] = None,
        key_dir: Optional[str] = None,
        handshake_timeout: float = 10.0,
        callback_timeout: float = 5.0,
        **kwargs
    ):
        """
        初始化 OpenClaw 客户端
        
        Args:
            client_id: 客户端标识
            base_url: 基础 URL
            ws_url: WebSocket URL（可选）
            token: 认证令牌
            scopes: 权限范围
            key_dir: 密钥目录
            handshake_timeout: 握手超时时间（秒）
            callback_timeout: 回调执行超时时间（秒）
            **kwargs: 其他参数传递给基类
        """
        if not ws_url and base_url:
            parsed = urlparse(base_url)
            if parsed.scheme not in ("ws", "wss"):
                raise ValueError("OpenClawWsClient 仅支持 ws/wss 协议，请通过 ws_url 配置")
            path = parsed.path.rstrip("/") or ""
            ws_url = f"{parsed.scheme}://{parsed.netloc}{path}"
        if ws_url:
            parsed_ws = urlparse(ws_url)
            if parsed_ws.scheme not in ("ws", "wss"):
                raise ValueError("OpenClawWsClient 的 ws_url 必须是 ws:// 或 wss://")
        
        super().__init__(
            client_id=client_id,
            ws_url=ws_url,
            **kwargs
        )
        
        self.base_url = base_url
        self.token = token.strip() if token else None
        self.scopes = scopes or ["operator.read", "operator.write"]
        self._device = DeviceIdentityManager(key_dir=key_dir)
        self._handshake_timeout = handshake_timeout
        self._callback_timeout = callback_timeout
    
    def _get_sign_token(self) -> Optional[str]:
        """获取用于签名的令牌"""
        cached_token = self._device.load_device_token()
        return self.token if not cached_token else cached_token
    
    async def _handshake(self) -> None:
        """执行握手认证（带完整的超时控制）"""
        try:
            # 1. 接收挑战（带超时）
            try:
                raw = await asyncio.wait_for(
                    self._ws.recv(),
                    timeout=self._handshake_timeout
                )
            except asyncio.TimeoutError:
                raise TimeoutError(f"握手超时：等待服务器挑战（{self._handshake_timeout}s）")
            
            # 2. 解析挑战数据
            try:
                challenge = json.loads(raw)
                nonce = challenge.get("payload", {}).get("nonce")
                if not nonce:
                    raise OpenClawHandshakeError("挑战数据缺少 nonce 字段")
            except json.JSONDecodeError:
                raise OpenClawHandshakeError("挑战数据格式错误（非 JSON）")
            
            # 3. 计算签名（在线程池中执行，避免阻塞事件循环）
            try:
                sign_token = self._get_sign_token()
                
                # 使用线程池执行签名计算（可能涉及磁盘IO）
                sig_b64, signed_at = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None,  # 使用默认线程池
                        lambda: self._device.sign(
                            nonce=nonce,
                            role="operator",
                            scopes=self.scopes,
                            token=sign_token,
                            client_id=self.CLIENT_ID,
                            client_mode=self.CLIENT_MODE,
                        )
                    ),
                    timeout=self._handshake_timeout / 2  # 签名计算最多占一半时间
                )
            except asyncio.TimeoutError:
                raise TimeoutError("握手超时：签名计算耗时过长")
            except Exception as e:
                raise OpenClawHandshakeError(f"签名计算失败: {e}")
            
            # 4. 构建认证载荷
            auth_payload = {}
            cached_token = self._device.load_device_token()
            if cached_token:
                auth_payload["token"] = cached_token
            elif self.token:
                auth_payload["token"] = self.token
            
            # 5. 发送连接请求（带超时）
            try:
                connect_frame = {
                    "minProtocol": self.MIN_PROTOCOL,
                    "maxProtocol": self.MAX_PROTOCOL,
                    "client": {
                        "id": self.CLIENT_ID,
                        "mode": self.CLIENT_MODE,
                        "version": self.CLIENT_VERSION,
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
                }
                
                # 使用基类的 request 方法发送连接请求
                response = await asyncio.wait_for(
                    self.request("connect", connect_frame, timeout=self._handshake_timeout),
                    timeout=self._handshake_timeout
                )
                
            except asyncio.TimeoutError:
                raise TimeoutError("握手超时：发送连接请求或等待响应")
            except Exception as e:
                raise OpenClawHandshakeError(f"连接请求失败: {e}")
            
            # 6. 处理响应中的新令牌
            try:
                auth_info = response.get("auth", {})
                if new_token := auth_info.get("deviceToken"):
                    self._device.save_device_token(new_token, "operator", self.scopes)
                    logger.info(f"[{self.client_id}] 收到新的设备令牌并已缓存")
            except Exception as e:
                logger.warning(f"[{self.client_id}] 保存设备令牌失败: {e}")
            
            logger.info(f"[{self.client_id}] 握手认证成功")
            
        except (TimeoutError, OpenClawHandshakeError):
            # 透传自定义异常
            raise
        except Exception as e:
            raise OpenClawHandshakeError(f"握手过程发生未知错误: {e}")
    
    async def _after_connect(self) -> None:
        """连接后执行握手认证（重写基类方法）"""
        await self._handshake()
    
    async def _safe_callback(self, callback, *args, **kwargs) -> None:
        """带超时控制的安全回调执行（重写基类方法）"""
        try:
            await asyncio.wait_for(
                callback(*args, **kwargs),
                timeout=self._callback_timeout
            )
        except asyncio.TimeoutError:
            logger.error(f"[{self.client_id}] 回调执行超时（{self._callback_timeout}s）")
        except Exception as e:
            logger.error(f"[{self.client_id}] 回调执行失败: {e}")
    
    async def _reconnect_loop(self) -> None:
        """带超时控制的重连循环（重写基类方法）"""
        if self.max_reconnect_attempts > 0 and self._reconnect_count >= self.max_reconnect_attempts:
            logger.error(f"[{self.client_id}] 重连失败：已达最大尝试次数 {self.max_reconnect_attempts}")
            return
        
        self._reconnect_count += 1
        delay = min(self.reconnect_delay * (2 ** (self._reconnect_count - 1)), 60)
        logger.info(f"[{self.client_id}] 将在 {delay}s 后第 {self._reconnect_count} 次重连")
        
        try:
            # 重连等待也加入超时控制
            await asyncio.wait_for(
                asyncio.sleep(delay),
                timeout=delay + 1  # 额外1秒缓冲
            )
        except asyncio.TimeoutError:
            logger.error(f"[{self.client_id}] 重连等待超时")
            return
        
        await self.connect()
    
    async def wait_for_connection(self, timeout: float = 30.0) -> bool:
        """
        等待连接建立完成
        """
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            if self.is_connected:
                return True
            await asyncio.sleep(0.1)
        
        raise TimeoutError(f"等待连接超时（{timeout}s）")
    
    async def execute_with_timeout(self, coro, timeout: float, error_msg: str = "操作超时"):
        """
        带超时控制的协程执行辅助方法
        
        Args:
            coro: 要执行的协程
            timeout: 超时时间（秒）
            error_msg: 超时错误信息
        """
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            raise TimeoutError(f"{error_msg}（{timeout}s）")
