import json
import logging
from typing import Any, Optional, Awaitable, Callable
from app.core.redis import get_redis_connection

logger = logging.getLogger(__name__)

class RedisQueue:
    def __init__(self, queue_name: str):
        self.queue_name = queue_name

    async def push(self, item: Any) -> None:
        """Push an item to the left of the list (queue)"""
        redis = await get_redis_connection()
        await redis.lpush(self.queue_name, json.dumps(item))

    async def pop(self, timeout: int = 0) -> Optional[Any]:
        """Pop an item from the right of the list (queue) - blocking"""
        redis = await get_redis_connection()
        # brpop returns (queue_name, item) or None if timeout
        result = await redis.brpop(self.queue_name, timeout=timeout)
        if result:
            return json.loads(result[1])
        return None

    async def length(self) -> int:
        redis = await get_redis_connection()
        return await redis.llen(self.queue_name)

class TaskQueue(RedisQueue):
    def __init__(self):
        super().__init__("task_queue")
