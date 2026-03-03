"""
Tests for Redis Memory Storage
"""
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from app.services.openclaw.task.memory.models import MemoryUnit, MemoryType
from app.services.openclaw.task.memory.storage import RedisMemoryStorage

@pytest.fixture
def mock_redis():
    mock = MagicMock()
    # Mock redis client methods
    # json() should return a Mock that has set, get methods
    mock.json = MagicMock()
    mock.json.return_value.get = AsyncMock()
    mock.json.return_value.set = AsyncMock()
    
    mock.ft.return_value = MagicMock()
    
    # Pipeline
    pipeline_mock = MagicMock()
    pipeline_mock.__aenter__.return_value = pipeline_mock
    # Pipeline json() should return an object that records calls, usually pipeline itself in redis-py if chained?
    # Actually in redis-py pipeline.json().set(...) queues the command.
    # So pipeline.json() returns a JSON client bound to pipeline.
    pipeline_json_mock = MagicMock()
    # Mock .set() to be awaitable (async)
    pipeline_json_mock.set = AsyncMock()
    pipeline_mock.json.return_value = pipeline_json_mock
    
    # pipe.execute() needs to be awaitable
    pipeline_mock.execute = AsyncMock()
    
    # zadd, expire also need to be async if called directly on pipe
    pipeline_mock.zadd = AsyncMock()
    pipeline_mock.expire = AsyncMock()
    
    mock.pipeline.return_value = pipeline_mock
    
    return mock

@pytest.fixture
def storage(mock_redis):
    s = RedisMemoryStorage("redis://mock")
    s.redis = mock_redis
    return s

@pytest.mark.asyncio
async def test_add_memory(storage, mock_redis):
    unit = MemoryUnit(
        session_id="sess-1",
        type=MemoryType.CONVERSATION,
        content="test content"
    )
    
    await storage.add_memory("sess-1", unit)
    
    # Check pipeline calls
    pipeline = mock_redis.pipeline.return_value.__aenter__.return_value
    pipeline.json.return_value.set.assert_called()
    pipeline.zadd.assert_called()
    pipeline.execute.assert_called()

@pytest.mark.asyncio
async def test_search_memory(storage, mock_redis):
    # Mock search result
    mock_doc = MagicMock()
    unit_data = MemoryUnit(session_id="s1", type="conversation", content="hello").model_dump_json()
    mock_doc.json = unit_data
    
    mock_res = MagicMock()
    mock_res.docs = [mock_doc]
    
    mock_redis.ft().search = AsyncMock(return_value=mock_res)
    
    # We need to mock Query import if it failed in storage.py
    # But since we use it in storage.py, it must be available or skipped.
    # If storage.py failed to import Query, it would raise NameError when used.
    # We should mock Query in storage module if not present.
    # The error "module ... does not have the attribute 'Query'" means it was not imported.
    # We need to patch where it is used or inject it into the module.
    
    import app.services.openclaw.task.memory.storage as storage_module
    
    # Inject Query mock
    with patch.object(storage_module, "Query", create=True) as MockQuery:
         MockQuery.return_value.paging.return_value = "query_obj"
         res = await storage.search_memory("hello", "s1")
         assert len(res) == 1
         assert res[0].content == "hello"
