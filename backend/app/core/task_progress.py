import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from app.core.redis import get_redis_connection

logger = logging.getLogger(__name__)

PROGRESS_KEY_PREFIX = "task:progress:"
PROGRESS_TTL = 24 * 60 * 60
PROGRESS_FINAL_TTL = 7 * 24 * 60 * 60


class TaskProgress:
    def __init__(self):
        self.redis = None

    async def _get_redis(self):
        if self.redis is None:
            self.redis = await get_redis_connection()
        return self.redis

    def _key(self, task_id: str) -> str:
        return f"{PROGRESS_KEY_PREFIX}{task_id}"

    async def set_progress(
        self,
        task_id: str,
        percent: int,
        status: str,
        msg: str = "",
        step: str = "",
        extend: Optional[Dict[str, Any]] = None
    ) -> None:
        redis = await self._get_redis()
        key = self._key(task_id)

        data = {
            "percent": str(percent),
            "status": status,
            "msg": msg,
            "step": step,
            "ts": datetime.now().isoformat(),
            "extend": json.dumps(extend or {})
        }

        try:
            await redis.hset(key, mapping=data)
            if status in ("SUCCESS", "FAILED", "CANCELLED"):
                await redis.expire(key, PROGRESS_FINAL_TTL)
            else:
                await redis.expire(key, PROGRESS_TTL)
        except Exception as e:
            logger.error(f"Failed to set progress for {task_id}: {e}")

    async def get_progress(self, task_id: str) -> Optional[Dict[str, Any]]:
        redis = await self._get_redis()
        key = self._key(task_id)

        try:
            data = await redis.hgetall(key)
            if not data:
                return None

            result = {
                "percent": int(data.get("percent", 0)),
                "status": data.get("status", "UNKNOWN"),
                "msg": data.get("msg", ""),
                "step": data.get("step", ""),
                "ts": data.get("ts", ""),
                "extend": json.loads(data.get("extend", "{}"))
            }
            return result
        except Exception as e:
            logger.error(f"Failed to get progress for {task_id}: {e}")
            return None

    async def delete_progress(self, task_id: str) -> None:
        redis = await self._get_redis()
        key = self._key(task_id)

        try:
            await redis.unlink(key)
        except Exception as e:
            logger.error(f"Failed to delete progress for {task_id}: {e}")

    async def publish_update(self, task_id: str, user_id: str) -> None:
        redis = await self._get_redis()
        channel = f"task:updates:{user_id}"

        try:
            progress = await self.get_progress(task_id)
            if progress:
                message = json.dumps({
                    "taskId": task_id,
                    **progress
                })
                await redis.publish(channel, message)
        except Exception as e:
            logger.error(f"Failed to publish update for {task_id}: {e}")


task_progress = TaskProgress()