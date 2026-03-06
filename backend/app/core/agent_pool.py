from cachetools import TTLCache
import logging

logger = logging.getLogger(__name__)

class AgentPool:
    """
    LRU/TTL Cache for Agent instances to avoid re-initialization overhead.
    """
    def __init__(self, max_size=100, ttl=300):
        # Cache up to 100 agents, expire after 5 minutes of inactivity
        self.cache = TTLCache(maxsize=max_size, ttl=ttl)

    def get(self, key: str):
        agent = self.cache.get(key)
        if agent:
            logger.debug(f"Agent cache hit for {key}")
        return agent

    def put(self, key: str, value: any):
        logger.debug(f"Agent cache miss/put for {key}")
        self.cache[key] = value

    def invalidate(self, key: str):
        if key in self.cache:
            del self.cache[key]

agent_pool = AgentPool()
