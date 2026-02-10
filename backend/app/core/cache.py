import asyncio
import json
import time
from typing import Any, Optional

import redis.asyncio as redis

from app.core.config import settings


class _MemoryEntry:
    __slots__ = ("value", "expires_at")

    def __init__(self, value: Any, expires_at: float):
        self.value = value
        self.expires_at = expires_at


class Cache:
    def __init__(self):
        self._redis: Optional[redis.Redis] = None
        self._memory: dict[str, _MemoryEntry] = {}
        self._lock = asyncio.Lock()

    async def _get_redis(self) -> Optional[redis.Redis]:
        if self._redis is not None:
            return self._redis
        try:
            client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)
            await client.ping()
            self._redis = client
            return self._redis
        except Exception:
            self._redis = None
            return None

    async def get_json(self, key: str) -> Optional[Any]:
        client = await self._get_redis()
        if client is not None:
            raw = await client.get(key)
            if raw is None:
                return None
            return json.loads(raw)

        async with self._lock:
            entry = self._memory.get(key)
            if entry is None:
                return None
            if entry.expires_at < time.time():
                self._memory.pop(key, None)
                return None
            return entry.value

    async def set_json(self, key: str, value: Any, ttl_seconds: int) -> None:
        client = await self._get_redis()
        if client is not None:
            await client.set(key, json.dumps(value, ensure_ascii=False), ex=ttl_seconds)
            return

        async with self._lock:
            self._memory[key] = _MemoryEntry(value=value, expires_at=time.time() + ttl_seconds)

    async def delete(self, key: str) -> None:
        client = await self._get_redis()
        if client is not None:
            await client.delete(key)
            return
        async with self._lock:
            self._memory.pop(key, None)


cache = Cache()

