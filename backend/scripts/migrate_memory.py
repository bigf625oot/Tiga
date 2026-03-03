"""
Redis Memory Migration Tool

Migrates existing in-memory session data (if any) to Redis.
Also initializes the Redis Search Index.
"""

import asyncio
import os
import sys

# Add backend path to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.services.openclaw.task.memory.storage import RedisMemoryStorage
from app.services.openclaw.task.session.session_manager import _SESSION_CACHE, TaskSessionManager

async def migrate_sessions(storage: RedisMemoryStorage):
    """
    Migrate in-memory sessions to Redis.
    """
    print(f"Found {len(_SESSION_CACHE)} sessions in memory.")
    
    # In a real scenario, we might need to persist _SESSION_CACHE to Redis Hash.
    # The current RedisMemoryStorage handles 'MemoryUnit', not 'TaskSession'.
    # We should add session storage capability to RedisMemoryStorage or separate class.
    # For now, let's assume we just want to ensure the Index is created.
    
    # To fully support session migration, we'd need to map _SESSION_CACHE structure to Redis.
    # _SESSION_CACHE = {session_id: {"node_id": str, "updated_at": datetime, "metadata": dict}}
    
    async with storage.redis.pipeline(transaction=True) as pipe:
        count = 0
        for session_id, data in _SESSION_CACHE.items():
            key = f"openclaw:session:{session_id}:meta"
            # HSET
            # Convert datetime to timestamp
            ts = data["updated_at"].timestamp()
            mapping = {
                "node_id": data["node_id"],
                "updated_at": ts,
                # Flatten metadata or store as json string
            }
            if data.get("metadata"):
                import json
                mapping["metadata"] = json.dumps(data["metadata"])
                
            pipe.hset(key, mapping=mapping)
            pipe.expire(key, 24 * 3600) # 24h TTL
            
            count += 1
            if count % 100 == 0:
                await pipe.execute()
                print(f"Migrated {count} sessions...")
        
        if count % 100 != 0:
            await pipe.execute()
            
    print(f"Migration complete. Total {count} sessions.")

async def main():
    redis_url = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")
    print(f"Connecting to Redis: {redis_url}")
    
    storage = RedisMemoryStorage(redis_url)
    
    print("Initializing Search Index...")
    await storage.initialize()
    print("Index initialized.")
    
    print("Starting Migration...")
    await migrate_sessions(storage)
    
    print("Done.")

if __name__ == "__main__":
    asyncio.run(main())
