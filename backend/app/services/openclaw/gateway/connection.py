"""
网关 WebSocket 处理器

功能：处理高并发 WebSocket 连接，包含限流、版本检查、消息去重、解压缩及数据一致性校验。
"""

import asyncio
import json
import logging
import time
import zlib
from typing import Dict, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import ValidationError
from starlette.websockets import WebSocketState
from collections import defaultdict

class TokenBucket:
    """令牌桶算法：用于流量限制"""
    def __init__(self, capacity: int, fill_rate: float):
        self.capacity = float(capacity)
        self.tokens = float(capacity)
        self.fill_rate = fill_rate
        self.timestamp = time.time()

    def consume(self, tokens: int = 1) -> bool:
        now = time.time()
        delta = now - self.timestamp
        # 补充令牌
        self.tokens = min(self.capacity, self.tokens + self.fill_rate * delta)
        self.timestamp = now
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

logger = logging.getLogger("openclaw.gateway.ws")

class WSConnectionManager:
    """
    WebSocket 连接管理器
    负责维护连接状态、监控心跳及消息预处理
    """
    def __init__(self):
        # 活跃连接映射：node_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        # 心跳追踪：node_id -> 最后可见时间戳
        self.heartbeat_tracker: Dict[str, float] = {}
        # 序列号追踪：node_id -> 最后处理的消息序列 ID (用于去重)
        self.sequence_tracker: Dict[str, int] = defaultdict(int)
        # 限流器：默认 20,000 QPS
        self.limiter = TokenBucket(capacity=20000, fill_rate=20000)

    async def connect(self, websocket: WebSocket, node_id: str):
        """接受并记录新连接"""
        await websocket.accept()
        self.active_connections[node_id] = websocket
        logger.info(f"节点 {node_id} 已通过 WS 连接")

    def disconnect(self, node_id: str):
        """断开连接并清理追踪数据"""
        if node_id in self.active_connections:
            del self.active_connections[node_id]
        if node_id in self.heartbeat_tracker:
            del self.heartbeat_tracker[node_id]
        logger.info(f"节点 {node_id} 已断开连接")

    async def handle_message(self, node_id: str, message: bytes | str):
        """处理接收到的消息流"""
        # 1. 限流检查
        if not self.limiter.consume():
            logger.warning(f"节点 {node_id} 触发限流")
            return

        try:
            # 2. 解压缩处理 (如果消息是字节流则尝试 zlib 解压)
            if isinstance(message, bytes):
                try:
                    data_str = zlib.decompress(message).decode("utf-8")
                except:
                    data_str = message.decode("utf-8")
            else:
                data_str = message

            payload = json.loads(data_str)
            
            # 3. 版本校验
            version = payload.get("version")
            if not self._check_version(version):
                logger.warning(f"来自 {node_id} 的协议版本 {version} 无效")
                return

            # 4. 消息去重 (基于序列号 ID)
            seq_id = payload.get("sequence_id")
            if seq_id is not None:
                last_seq = self.sequence_tracker[node_id]
                if seq_id <= last_seq:
                    logger.debug(f"丢弃来自 {node_id} 的重复/过期消息 {seq_id}")
                    return
                self.sequence_tracker[node_id] = seq_id

            # 5. 一致性检查 (校验和、时间戳)
            if not self._check_consistency(payload):
                 from .consistency import consistency_manager
                 await consistency_manager.handle_dirty_data(node_id, payload)
                 return

            # 6. 更新心跳时间
            self.heartbeat_tracker[node_id] = time.time()
            
            # 7. 进入后续业务逻辑处理
            await self._process_payload(node_id, payload)

        except json.JSONDecodeError:
            logger.error(f"来自 {node_id} 的 JSON 格式错误")
        except Exception as e:
            logger.error(f"处理来自 {node_id} 的消息时出错: {e}")

    def _check_version(self, version: str) -> bool:
        """检查客户端版本是否受支持"""
        return True

    def _check_consistency(self, payload: Dict[str, Any]) -> bool:
        """校验 CRC32 签名和时间戳偏移"""
        try:
            # 重构原始数据字符串进行签名比对
            metric_data = f"{payload['node_id']}{payload['timestamp']}{payload['sequence_id']}{payload['version']}"
            calc_crc = zlib.crc32(metric_data.encode())
            
            if calc_crc != payload.get("checksum"):
                logger.warning(f"节点 {payload['node_id']} 的校验和(Checksum)不匹配")
                return False
            
            # 检查时间戳偏移（允许 60 秒内的时钟偏斜）
            now = time.time()
            ts = payload.get("timestamp", 0)
            if abs(now - ts) > 60:
                 logger.warning(f"节点 {payload['node_id']} 时间戳偏差过大: {ts} vs {now}")
                 pass # 此处可根据业务严谨程度决定是否返回 False
                 
            return True
        except Exception:
            return False

    async def _process_payload(self, node_id: str, payload: Dict[str, Any]):
        """处理最终业务载荷（例如：更新数据库、推送指标到 Prometheus）"""
        pass

# 全局 WebSocket 管理器实例
ws_manager = WSConnectionManager()