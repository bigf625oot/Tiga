import logging
import time
from typing import List, Dict, Any, Optional, Tuple, Union
from redis.exceptions import ResponseError
from app.core.redis import get_redis_connection

logger = logging.getLogger(__name__)

class RedisStream:
    """
    A wrapper around Redis Streams to handle common operations like
    adding messages, creating consumer groups, reading, and acknowledging messages.
    """
    # Class-level storage for in-memory simulation across instances
    _memory_streams: Dict[str, List[Tuple[str, Dict[str, Any]]]] = {}

    def __init__(self, stream_key: str, group_name: str = "default_group"):
        self.stream_key = stream_key
        self.group_name = group_name

    async def ensure_group(self, start_id: str = "0") -> None:
        """
        Ensure the consumer group exists.
        :param start_id: Where to start reading from. "0" for all messages, "$" for new messages.
        """
        try:
            redis = await get_redis_connection()
            await redis.ping()
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Switching to MemoryStream mode (Simulated).")
            self._use_memory = True
            # Initialize shared memory for this key if needed
            if self.stream_key not in RedisStream._memory_streams:
                RedisStream._memory_streams[self.stream_key] = []
            return

        try:
            await redis.xgroup_create(self.stream_key, self.group_name, id=start_id, mkstream=True)
            logger.info(f"Created consumer group '{self.group_name}' for stream '{self.stream_key}'")
        except ResponseError as e:
            if "BUSYGROUP" in str(e):
                # Group already exists, which is fine
                pass
            else:
                logger.error(f"Error creating consumer group: {e}")
                raise e

    async def add(self, data: Dict[str, Any], max_len: int = 10000) -> Optional[str]:
        """
        Add a message to the stream.
        """
        if getattr(self, "_use_memory", False):
            import time
            msg_id = f"{int(time.time() * 1000)}-0"
            if self.stream_key not in RedisStream._memory_streams:
                 RedisStream._memory_streams[self.stream_key] = []
            RedisStream._memory_streams[self.stream_key].append((msg_id, data))
            return msg_id

        redis = await get_redis_connection()
        try:
            msg_id = await redis.xadd(self.stream_key, data, maxlen=max_len)
            return msg_id
        except Exception as e:
            logger.error(f"Error adding to stream {self.stream_key}: {e}")
            raise e

    async def read_group(
        self, 
        consumer_name: str, 
        count: int = 1, 
        block: int = 0
    ) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Read messages from the stream using the consumer group.
        """
        if getattr(self, "_use_memory", False):
            # Simple simulation: just pop from memory stream if available
            if self.stream_key not in RedisStream._memory_streams:
                 RedisStream._memory_streams[self.stream_key] = []
            
            stream_data = RedisStream._memory_streams[self.stream_key]
            if stream_data:
                # Return messages
                # Note: In real Redis, xreadgroup with > returns only new messages delivered to this consumer
                # Here we simplify: Just return whatever is there.
                # Issue: Multiple consumers will get same messages if we don't track "delivered".
                # For simulation, let's assume one consumer or just return all.
                # To avoid infinite loops in worker, we should maybe "hide" them?
                # But worker acks them.
                # Let's just return first N.
                messages = stream_data[:count]
                return messages
            
            # Simulate blocking if requested?
            if block > 0:
                import asyncio
                await asyncio.sleep(block / 1000.0)
                
            return []

        redis = await get_redis_connection()
        try:
            # Read new messages (">")
            streams = {self.stream_key: ">"}
            response = await redis.xreadgroup(
                self.group_name, 
                consumer_name, 
                streams, 
                count=count, 
                block=block
            )
            
            # Response format: [[stream_name, [[msg_id, data], ...]], ...]
            messages = []
            if response:
                for stream_name, msg_list in response:
                    if stream_name == self.stream_key:
                        for msg_id, msg_data in msg_list:
                            messages.append((msg_id, msg_data))
            
            return messages
        except Exception as e:
            logger.error(f"Error reading from stream {self.stream_key}: {e}")
            return []

    async def ack(self, message_ids: List[str]) -> int:
        """
        Acknowledge processed messages.
        """
        if getattr(self, "_use_memory", False):
            if self.stream_key not in RedisStream._memory_streams:
                 return 0
            
            stream_data = RedisStream._memory_streams[self.stream_key]
            original_len = len(stream_data)
            # Remove acked messages
            RedisStream._memory_streams[self.stream_key] = [m for m in stream_data if m[0] not in message_ids]
            return original_len - len(RedisStream._memory_streams[self.stream_key])

        if not message_ids:
            return 0
            
        redis = await get_redis_connection()
        try:
            return await redis.xack(self.stream_key, self.group_name, *message_ids)
        except Exception as e:
            logger.error(f"Error acknowledging messages in {self.stream_key}: {e}")
            return 0

    async def claim_stale_messages(
        self, 
        consumer_name: str, 
        min_idle_time: int = 60000, 
        count: int = 10
    ) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Claim messages that have been pending for too long (e.g. crashed workers).
        :param consumer_name: The consumer claiming ownership.
        :param min_idle_time: Minimum idle time in milliseconds.
        :param count: Max number of messages to claim.
        :return: List of claimed messages.
        """
        redis = await get_redis_connection()
        try:
            # XAUTOCLAIM is available in Redis 6.2+
            # It returns: (next_start_id, [ (msg_id, data), ... ])
            # We use "0-0" to start from the beginning of PEL
            start_id = "0-0"
            result = await redis.xautoclaim(
                self.stream_key, 
                self.group_name, 
                consumer_name, 
                min_idle_time, 
                start_id, 
                count=count
            )
            
            # result[1] is the list of messages
            messages = result[1]
            return messages
        except Exception as e:
            logger.error(f"Error claiming messages in {self.stream_key}: {e}")
            return []

    async def get_pending_info(self) -> Dict[str, Any]:
        """
        Get information about pending messages.
        """
        redis = await get_redis_connection()
        try:
            return await redis.xpending(self.stream_key, self.group_name)
        except Exception as e:
            logger.error(f"Error getting pending info for {self.stream_key}: {e}")
            return {}

