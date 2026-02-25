
import pytest
import json
from unittest.mock import MagicMock, AsyncMock, patch
from app.services.data.vanna.service import SmartDataQueryService
import pandas as pd

@pytest.fixture
def mock_service():
    # Patch the class-level _instance to ensure we get a fresh instance or our mocked one if get_instance is called
    # But here we can just instantiate it directly for unit testing logic inside query
    
    # We need to mock VannaCore inside the service
    with patch('app.services.data.vanna.service.VannaCore') as MockVannaCore:
        # Create instance
        service = SmartDataQueryService()
        service.vanna_core = MockVannaCore.return_value
        
        # Mock sql_runner to be truthy so we don't get "Please connect" immediately
        service.vanna_core.sql_runner = MagicMock()
        
        # Mock methods called during query
        service.vanna_core.classify_intent.return_value = "Data Query"
        service.vanna_core.generate_sql.return_value = "SELECT * FROM users"
        service.vanna_core.run_sql.return_value = pd.DataFrame({"id": [1], "name": ["Test"]})
        service.vanna_core.generate_echarts.return_value = {"chart": "config"}
        
        # Mock add_message to avoid DB calls
        service.add_message = AsyncMock()
        
        yield service

@pytest.mark.asyncio
async def test_query_sequence_happy_path(mock_service):
    """Verify that steps are sequential and formatted correctly in a successful run."""
    
    question = "Show me users"
    
    # Collect all yielded messages
    messages = []
    async for item in mock_service.query(question):
        messages.append(json.loads(item))
        
    # Check if we got messages
    assert len(messages) > 0
    
    # Verify step sequence
    steps = [msg["step"] for msg in messages]
    assert steps == list(range(1, len(steps) + 1))
    
    # Verify content presence and types
    assert any("正在分析" in msg["content"] and msg["type"] == "process" for msg in messages)
    assert any("SELECT * FROM users" in msg["content"] and msg["type"] == "sql" for msg in messages)
    assert any("echarts" in msg["content"] and msg["type"] == "chart" for msg in messages)
    # Check data type
    assert any("查询结果" in msg["content"] and msg["type"] == "data" for msg in messages)

@pytest.mark.asyncio
async def test_query_sequence_no_db_connection(mock_service):
    """Verify sequence when DB is not connected."""
    mock_service.vanna_core.sql_runner = None
    
    messages = []
    async for item in mock_service.query("Any question"):
        messages.append(json.loads(item))
        
    assert len(messages) == 1
    assert messages[0]["step"] == 1
    assert "请先连接到数据库" in messages[0]["content"]

@pytest.mark.asyncio
async def test_query_sequence_exception(mock_service):
    """Verify sequence when an exception occurs."""
    mock_service.vanna_core.classify_intent.side_effect = Exception("Intent Error")
    
    messages = []
    async for item in mock_service.query("Any question"):
        messages.append(json.loads(item))
        
    # Should have the first message (start analysis) and then the error message
    assert len(messages) >= 2
    assert messages[-1]["content"] == "错误：Intent Error"
    
    # Verify sequence continuity
    steps = [msg["step"] for msg in messages]
    assert steps == list(range(1, len(steps) + 1))

@pytest.mark.asyncio
async def test_query_sequence_invalid_sql(mock_service):
    """Verify sequence when SQL generation fails (returns comment)."""
    mock_service.vanna_core.generate_sql.return_value = "-- No SQL generated"
    
    messages = []
    async for item in mock_service.query("Hard question"):
        messages.append(json.loads(item))
        
    # Check for specific failure message
    assert any("未能生成有效的 SQL" in msg["content"] for msg in messages)
    
    # Verify sequence
    steps = [msg["step"] for msg in messages]
    assert steps == list(range(1, len(steps) + 1))
