import json
import logging
from typing import Dict, Set, Optional
from fastapi import WebSocket
import asyncio

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self):
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            if user_id not in self._connections:
                self._connections[user_id] = set()
            self._connections[user_id].add(websocket)
        logger.info(f"WebSocket connected for user {user_id}")

    async def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            if user_id in self._connections:
                self._connections[user_id].discard(websocket)
                if not self._connections[user_id]:
                    del self._connections[user_id]
        logger.info(f"WebSocket disconnected for user {user_id}")

    async def send_to_user(self, user_id: str, message: dict) -> None:
        if user_id not in self._connections:
            return

        dead_connections = set()
        message_str = json.dumps(message, default=str)

        async with self._lock:
            connections = self._connections.get(user_id, set()).copy()

        for websocket in connections:
            try:
                await websocket.send_text(message_str)
            except Exception as e:
                logger.warning(f"Failed to send to WebSocket: {e}")
                dead_connections.add(websocket)

        if dead_connections:
            async with self._lock:
                for ws in dead_connections:
                    if user_id in self._connections:
                        self._connections[user_id].discard(ws)

    async def broadcast(self, message: dict) -> None:
        message_str = json.dumps(message, default=str)
        async with self._lock:
            all_connections = [
                (user_id, ws)
                for user_id, connections in self._connections.items()
                for ws in connections
            ]

        for user_id, websocket in all_connections:
            try:
                await websocket.send_text(message_str)
            except Exception:
                pass


ws_manager = WebSocketManager()