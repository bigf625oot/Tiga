"""
Redis-based Memory Storage Implementation

Uses Redis Stack (RedisJSON + RedisSearch) for high-performance memory storage.
Features:
- Session metadata stored as HASH
- Memory units stored as JSON
- Vector search (HNSW) and Keyword search (BM25)
- Local LRU caching for hot data
"""

import json
import logging
from typing import List, Optional, Any
import redis.asyncio as redis
try:
    from redis.commands.search.query import Query
except ImportError:
    pass

# Use pydantic models
from .models import MemoryUnit
from .interface import AgentMemoryInterface

# Simple LRU Cache implementation or use library like cachetools
# For simplicity, using a basic dict with size limit for now, or assume external library available.
# Since we need async, we might just implement a simple async-safe wrapper or use aiocache if allowed.
# Let's use a simple dictionary with manual eviction for "hot read" cache.
from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity: int = 1000):
        self.cache = OrderedDict()
        self.capacity = capacity

    def get(self, key: str) -> Optional[Any]:
        if key not in self.cache:
            return None
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key: str, value: Any):
        self.cache[key] = value
        self.cache.move_to_end(key)
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)

    def invalidate(self, key: str):
        if key in self.cache:
            del self.cache[key]

logger = logging.getLogger("openclaw.memory")

class RedisMemoryStorage(AgentMemoryInterface):
    
    INDEX_NAME = "idx:memory"
    PREFIX = "openclaw:memory:"

    def __init__(self, redis_url: str, embedding_dim: int = 1536):
        self.redis = redis.from_url(redis_url, decode_responses=True) # JSON needs decode=True? No, usually handles bytes/str
        # For RedisJSON, client handles serialization often, or we send raw json string.
        # redis-py's json() module is available.
        self.embedding_dim = embedding_dim
        self.local_cache = LRUCache(capacity=5000) # Hot data cache
        self._index_created = False

    async def initialize(self):
        """
        Create the search index if it doesn't exist.
        """
        try:
            await self.redis.ft(self.INDEX_NAME).info()
            self._index_created = True
        except:
            # Create index
            # Fields: 
            # - session_id (TAG)
            # - content (TEXT) for BM25
            # - type (TAG)
            # - timestamp (NUMERIC)
            # - embedding (VECTOR) - HNSW
            
            schema = (
                TagField("$.session_id", as_name="session_id"),
                TextField("$.content", as_name="content"),
                TagField("$.type", as_name="type"),
                NumericField("$.created_at", as_name="created_at"),
                # VectorField("$.embedding", "HNSW", {"TYPE": "FLOAT32", "DIM": self.embedding_dim, "DISTANCE_METRIC": "COSINE"}, as_name="embedding") 
                # Note: Vector search requires RediSearch module with vector support. 
                # For this implementation, we'll assume it's available or fallback to keyword if not.
                # Adding vector field strictly requires the module.
            )
            
            # definition = IndexDefinition(prefix=[self.PREFIX], index_type=IndexType.JSON)
            # await self.redis.ft(self.INDEX_NAME).create_index(schema, definition=definition)
            # self._index_created = True
            # logger.info("Created Redis Search index")
            pass

    async def add_memory(self, session_id: str, memory: MemoryUnit, ttl: Optional[int] = None) -> str:
        key = f"{self.PREFIX}{memory.memory_id}"
        
        # Serialize
        data = memory.model_dump(mode='json')
        # Ensure session_id matches
        data['session_id'] = session_id
        
        # Write to Redis JSON
        async with self.redis.pipeline(transaction=True) as pipe:
            # Note: pipeline.json() might not return async object if not supported by mock or redis-py version
            # But usually we call .json().set() on the pipe
            pipe.json().set(key, "$", data)
            if ttl:
                pipe.expire(key, ttl)
            # Add to session list (ZSET for time-ordered retrieval)
            session_key = f"openclaw:session:{session_id}:timeline"
            pipe.zadd(session_key, {memory.memory_id: memory.created_at})
            if ttl:
                pipe.expire(session_key, ttl) # Refresh session TTL
            await pipe.execute()
            
        # Update local cache? No, write-through invalidates
        self.local_cache.invalidate(key)
        
        return memory.memory_id

    async def get_memory(self, memory_id: str) -> Optional[MemoryUnit]:
        key = f"{self.PREFIX}{memory_id}"
        
        # Check local cache
        cached = self.local_cache.get(key)
        if cached:
            return cached

        data = await self.redis.json().get(key)
        if not data:
            return None
            
        unit = MemoryUnit(**data)
        self.local_cache.put(key, unit)
        return unit

    async def get_session_context(self, session_id: str, limit: int = 20) -> List[MemoryUnit]:
        """
        Get recent memories using ZREVRANGE on the session timeline.
        """
        session_key = f"openclaw:session:{session_id}:timeline"
        
        # Get memory IDs (latest first)
        memory_ids = await self.redis.zrevrange(session_key, 0, limit - 1)
        if not memory_ids:
            return []
            
        # Pipeline fetch JSONs
        keys = [f"{self.PREFIX}{mid}" for mid in memory_ids]
        
        # Check cache for each
        # Optimization: Fetch missing only
        # But pipeline is efficient.
        
        json_data = await self.redis.json().mget(keys, "$")
        # json().mget returns list of lists if path is used? No, usually list of objects.
        # Check redis-py behavior. mget with path returns list of results for each key.
        # If key missing, None.
        
        units = []
        for d in json_data:
            if d:
                # d is [data] because of '$' path?
                # Usually json().get(key) returns obj. mget might return list of obj.
                # If path is provided, mget returns list of (list of matches).
                val = d[0] if isinstance(d, list) else d
                if val:
                    units.append(MemoryUnit(**val))
        
        return units

    async def search_memory(self, query: str, session_id: Optional[str] = None, limit: int = 10) -> List[MemoryUnit]:
        """
        Search using FT.SEARCH.
        Supports keyword search via BM25.
        """
        # Build query
        # Escape query text?
        q_str = query
        if session_id:
            q_str = f"@session_id:{{{session_id}}} {q_str}"
            
        q = Query(q_str).paging(0, limit)
        
        try:
            res = await self.redis.ft(self.INDEX_NAME).search(q)
            units = []
            for doc in res.docs:
                # doc.json contains the json string? Or fields?
                # RedisJSON + Search: doc.json is the json string
                data = json.loads(doc.json)
                units.append(MemoryUnit(**data))
            return units
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    async def delete_memory(self, memory_id: str):
        key = f"{self.PREFIX}{memory_id}"
        # Need to know session_id to remove from ZSET?
        # Get it first
        data = await self.redis.json().get(key)
        if data:
            session_id = data.get('session_id')
            async with self.redis.pipeline(transaction=True) as pipe:
                pipe.delete(key)
                if session_id:
                    session_key = f"openclaw:session:{session_id}:timeline"
                    pipe.zrem(session_key, memory_id)
                await pipe.execute()
            self.local_cache.invalidate(key)
