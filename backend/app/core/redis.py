import redis.asyncio as redis
from typing import Optional
from app.core.config import settings

class RedisPool:
    _pool: Optional[redis.Redis] = None

    @classmethod
    async def get_redis(cls) -> redis.Redis:
        if cls._pool is None:
            # Check if REDIS_URL is set, otherwise construct from host/port
            url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0"
            cls._pool = redis.from_url(
                url,
                decode_responses=True,
                encoding="utf-8"
            )
        return cls._pool

    @classmethod
    async def close(cls):
        if cls._pool:
            await cls._pool.close()
            cls._pool = None

async def get_redis_connection() -> redis.Redis:
    return await RedisPool.get_redis()
