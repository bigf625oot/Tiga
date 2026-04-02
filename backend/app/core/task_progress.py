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
        try:
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

            await redis.hset(key, mapping=data)
            if status in ("SUCCESS", "FAILED", "CANCELLED"):
                await redis.expire(key, PROGRESS_FINAL_TTL)
            else:
                await redis.expire(key, PROGRESS_TTL)
        except Exception as e:
            logger.error(f"Failed to set progress for {task_id}: {e}")

    async def get_progress(self, task_id: str) -> Optional[Dict[str, Any]]:
        try:
            redis = await self._get_redis()
            key = self._key(task_id)
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
        try:
            redis = await self._get_redis()
            key = self._key(task_id)
            await redis.unlink(key)
        except Exception as e:
            logger.error(f"Failed to delete progress for {task_id}: {e}")

    async def publish_update(self, task_id: str, user_id: str) -> None:
        try:
            progress = await self.get_progress(task_id)
            if not progress:
                # If Redis is down, we can fetch from DB instead
                from app.db.session import AsyncSessionLocal
                from app.crud.async_task import async_task
                async with AsyncSessionLocal() as db:
                    task = await async_task.get(db, task_id)
                    if task:
                        progress = {
                            "percent": task.progress,
                            "status": task.status,
                            "msg": task.msg,
                            "step": task.step,
                            "extend": {}
                        }
            
            if progress:
                message = {
                    "task_id": task_id,
                    "type": "progress",
                    "data": progress
                }
                
                # Send via WebSocket Manager directly (works without Redis in single-instance mode)
                from app.core.websocket_manager import ws_manager
                await ws_manager.send_to_user(user_id, message)
                
                # Also publish to Redis for multi-instance support (ignore if Redis is down)
                redis = await self._get_redis()
                channel = f"task:updates:{user_id}"
                import json
                await redis.publish(channel, json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to publish update for {task_id}: {e}")


task_progress = TaskProgress()