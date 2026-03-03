import pytest
from unittest.mock import AsyncMock, patch
from app.core.redis_stream import RedisStream
from app.core.task_stream import TaskStream
import json

@pytest.mark.asyncio
async def test_redis_stream_add():
    mock_redis = AsyncMock()
    mock_redis.xadd.return_value = "123-0"
    
    with patch("app.core.redis_stream.get_redis_connection", return_value=mock_redis):
        stream = RedisStream("test_stream")
        msg_id = await stream.add({"key": "value"})
        
        assert msg_id == "123-0"
        mock_redis.xadd.assert_called_once_with("test_stream", {"key": "value"}, maxlen=10000)

@pytest.mark.asyncio
async def test_redis_stream_ensure_group():
    mock_redis = AsyncMock()
    
    with patch("app.core.redis_stream.get_redis_connection", return_value=mock_redis):
        stream = RedisStream("test_stream", "group1")
        await stream.ensure_group()
        
        mock_redis.xgroup_create.assert_called_once_with("test_stream", "group1", id="0", mkstream=True)

@pytest.mark.asyncio
async def test_redis_stream_read_group():
    mock_redis = AsyncMock()
    # Mock response: [[stream_name, [[msg_id, data], ...]], ...]
    mock_redis.xreadgroup.return_value = [
        ["test_stream", [("123-0", {"key": "value"})]]
    ]
    
    with patch("app.core.redis_stream.get_redis_connection", return_value=mock_redis):
        stream = RedisStream("test_stream", "group1")
        messages = await stream.read_group("consumer1")
        
        assert len(messages) == 1
        assert messages[0] == ("123-0", {"key": "value"})

@pytest.mark.asyncio
async def test_task_stream_push_pop():
    mock_redis = AsyncMock()
    mock_redis.xadd.return_value = "123-0"
    
    task_data = {"id": "task1", "name": "test"}
    payload = json.dumps(task_data)
    
    mock_redis.xreadgroup.return_value = [
        ["task_stream", [("123-0", {"payload": payload})]]
    ]
    
    with patch("app.core.redis_stream.get_redis_connection", return_value=mock_redis):
        stream = TaskStream()
        
        # Test Push
        msg_id = await stream.push_task(task_data)
        assert msg_id == "123-0"
        mock_redis.xadd.assert_called_once_with("task_stream", {"payload": payload}, maxlen=10000)
        
        # Test Pop
        popped_id, popped_data = await stream.pop_task("consumer1")
        assert popped_id == "123-0"
        assert popped_data == task_data
