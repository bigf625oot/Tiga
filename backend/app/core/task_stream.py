import json
import logging
from typing import Optional, Tuple, Dict, Any
from app.core.redis_stream import RedisStream

logger = logging.getLogger(__name__)

class TaskStream(RedisStream):
    """
    Specialized Redis Stream for task processing.
    """
    def __init__(self):
        # Stream key: task_stream
        # Consumer Group: task_workers
        super().__init__("task_stream", "task_workers")

    async def ensure_infrastructure(self):
        """
        Ensure the stream and consumer group exist.
        """
        await self.ensure_group(start_id="0")

    async def push_task(self, task_data: Dict[str, Any]) -> str:
        """
        Push a task to the stream.
        We serialize the entire task data into a JSON string under the 'payload' key.
        """
        try:
            payload = json.dumps(task_data)
            msg_id = await self.add({"payload": payload})
            return msg_id
        except Exception as e:
            logger.error(f"Failed to push task to stream: {e}")
            raise e

    async def pop_task(self, consumer_name: str, block: int = 2000) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        Pop a task for a specific consumer.
        Returns (message_id, task_data).
        """
        try:
            messages = await self.read_group(consumer_name, count=1, block=block)
            if messages:
                msg_id, data = messages[0]
                if "payload" in data:
                    return msg_id, json.loads(data["payload"])
                else:
                    logger.warning(f"Received malformed message {msg_id} without payload")
                    # Ack it so we don't process it again? Or move to DLQ?
                    # For now, let's just ack it to clear it
                    await self.ack([msg_id])
                    return None, None
            return None, None
        except Exception as e:
            logger.error(f"Failed to pop task from stream: {e}")
            return None, None

    async def ack_task(self, msg_id: str):
        """
        Acknowledge a task as processed.
        """
        await self.ack([msg_id])

task_stream = TaskStream()
