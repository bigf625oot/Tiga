import logging
from datetime import datetime, timedelta

from sqlalchemy import select, update, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.async_task import AsyncTask, AsyncTaskLog
from app.core.redis import get_redis_connection

logger = logging.getLogger(__name__)

FINAL_STATUSES = ["SUCCESS", "FAILED", "CANCELLED"]
HOT_DATA_DAYS = 7
COLD_DATA_DAYS = 90


class TaskLifecycleManager:
    def __init__(self):
        self.redis = None

    async def _get_redis(self):
        if self.redis is None:
            self.redis = await get_redis_connection()
        return self.redis

    async def archive_old_tasks(self, db: AsyncSession, days: int = HOT_DATA_DAYS) -> int:
        cutoff = datetime.now() - timedelta(days=days)

        result = await db.execute(
            update(AsyncTask)
            .where(
                and_(
                    AsyncTask.deleted == False,
                    AsyncTask.status.in_(FINAL_STATUSES),
                    AsyncTask.updated_at < cutoff
                )
            )
            .values(deleted=True)
        )
        await db.commit()
        count = result.rowcount

        if count > 0:
            logger.info(f"Archived {count} tasks older than {days} days")

        return count

    async def delete_cold_tasks(self, db: AsyncSession, days: int = COLD_DATA_DAYS) -> int:
        cutoff = datetime.now() - timedelta(days=days)

        result = await db.execute(
            delete(AsyncTask)
            .where(
                and_(
                    AsyncTask.deleted == True,
                    AsyncTask.updated_at < cutoff
                )
            )
        )
        await db.commit()
        count = result.rowcount

        if count > 0:
            logger.info(f"Permanently deleted {count} tasks older than {days} days")

        return count

    async def cleanup_old_logs(self, db: AsyncSession, days: int = 30) -> int:
        cutoff = datetime.now() - timedelta(days=days)

        result = await db.execute(
            delete(AsyncTaskLog)
            .where(AsyncTaskLog.created_at < cutoff)
        )
        await db.commit()
        count = result.rowcount

        if count > 0:
            logger.info(f"Deleted {count} task logs older than {days} days")

        return count

    async def cleanup_redis_progress_keys(self) -> int:
        redis = await self._get_redis()
        count = 0

        try:
            keys = await redis.keys("task:progress:*")
            for key in keys:
                ttl = await redis.ttl(key)
                if ttl == -1:
                    await redis.unlink(key)
                    count += 1

            if count > 0:
                logger.info(f"Cleaned up {count} orphaned Redis progress keys")

        except Exception as e:
            logger.error(f"Failed to cleanup Redis progress keys: {e}")

        return count

    async def get_task_stats(self, db: AsyncSession) -> dict:
        total = await db.execute(
            select(AsyncTask).filter(AsyncTask.deleted == False)
        )
        total_count = len(total.scalars().all())

        status_counts = {}
        for status in ["PENDING", "RUNNING", "SUCCESS", "FAILED", "CANCELLED"]:
            result = await db.execute(
                select(AsyncTask).filter(
                    and_(
                        AsyncTask.deleted == False,
                        AsyncTask.status == status
                    )
                )
            )
            status_counts[status] = len(result.scalars().all())

        return {
            "total": total_count,
            "by_status": status_counts,
            "hot_data_days": HOT_DATA_DAYS,
            "cold_data_days": COLD_DATA_DAYS
        }


lifecycle_manager = TaskLifecycleManager()