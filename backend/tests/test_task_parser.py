import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException

from app.services.openclaw.task.parser.task_parser_service import parse_task_intent, TASK_INTENT_SCHEMA
from app.services.openclaw.utils.parser.exception import TaskParsingError
from app.models.llm_model import LLMModel

# Mock LLM Response Helper
def mock_llm_response(content):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": content}}]
    }
    return mock_resp

@pytest.fixture
def mock_db_session():
    session = AsyncMock()
    # Mock LLM Model query
    mock_result = MagicMock()
    mock_model = LLMModel(api_key="test_key", base_url="http://test.com", model_id="gpt-test")
    mock_result.scalars.return_value.first.return_value = mock_model
    session.execute.return_value = mock_result
    return session

@pytest.mark.asyncio
async def test_parse_task_intent_success(mock_db_session):
    """测试一次性解析成功"""
    valid_json = json.dumps({
        "command": "crawl https://example.com",
        "schedule": "0 10 * * *",
        "node_requirements": "node-1"
    })
    
    with patch("httpx.AsyncClient.post", return_value=mock_llm_response(valid_json)):
        result = await parse_task_intent("test prompt", mock_db_session)
        
        assert result["command"] == "crawl https://example.com"
        assert result["schedule"] == "0 10 * * *"
        assert result["target_node"] == "node-1"

@pytest.mark.asyncio
async def test_parse_task_intent_default_values(mock_db_session):
    """测试默认值回退"""
    partial_json = json.dumps({"command": "monitor site"})
    
    with patch("httpx.AsyncClient.post", return_value=mock_llm_response(partial_json)):
        result = await parse_task_intent("test prompt", mock_db_session)
        
        assert result["command"] == "monitor site"
        assert result["schedule"] == "0 9 * * *"
        assert result["target_node"] == "default"

@pytest.mark.asyncio
async def test_parse_task_intent_retry_success(mock_db_session):
    """测试首次失败，重试成功"""
    invalid_json = "invalid json"
    valid_json = json.dumps({"command": "retry success"})
    
    # 模拟两次调用：第一次失败，第二次成功
    mock_post = AsyncMock(side_effect=[
        mock_llm_response(invalid_json),
        mock_llm_response(valid_json)
    ])
    
    with patch("httpx.AsyncClient.post", mock_post):
        result = await parse_task_intent("test prompt", mock_db_session)
        
        assert result["command"] == "retry success"
        assert mock_post.call_count == 2

@pytest.mark.asyncio
async def test_parse_task_intent_all_retries_failed(mock_db_session):
    """测试重试后仍失败，抛出自定义异常"""
    invalid_json = "still invalid"
    
    mock_post = AsyncMock(return_value=mock_llm_response(invalid_json))
    
    with patch("httpx.AsyncClient.post", mock_post):
        with pytest.raises(TaskParsingError) as exc:
            await parse_task_intent("test prompt", mock_db_session)
        
        assert exc.value.retry_count == 1
        assert "Task parsing failed" in str(exc.value)

@pytest.mark.asyncio
async def test_parse_task_intent_schema_validation_error(mock_db_session):
    """测试 Schema 校验失败（缺少必填字段）"""
    # 缺少 command 字段
    invalid_schema = json.dumps({"schedule": "0 9 * * *"})
    
    mock_post = AsyncMock(return_value=mock_llm_response(invalid_schema))
    
    with patch("httpx.AsyncClient.post", mock_post):
        with pytest.raises(TaskParsingError) as exc:
            await parse_task_intent("test prompt", mock_db_session)
            
        assert "command" in exc.value.validation_error

@pytest.mark.asyncio
@pytest.mark.parametrize("json_content, expected_node", [
    (json.dumps({"command": "c", "node_requirements": "node-A"}), "node-A"),
    (json.dumps({"command": "c", "node_requirements": "default"}), "default"),
    (json.dumps({"command": "c", "node_requirements": ""}), "default"),
    (json.dumps({"command": "c"}), "default"),
])
async def test_node_routing_logic(mock_db_session, json_content, expected_node):
    """参数化测试节点路由逻辑"""
    with patch("httpx.AsyncClient.post", return_value=mock_llm_response(json_content)):
        result = await parse_task_intent("test", mock_db_session)
        assert result["target_node"] == expected_node

@pytest.mark.asyncio
async def test_parse_task_intent_llm_error(mock_db_session):
    """测试 LLM 调用异常"""
    with patch("httpx.AsyncClient.post", side_effect=Exception("Network Error")):
        with pytest.raises(HTTPException) as exc:
            await parse_task_intent("test", mock_db_session)
        
        assert exc.value.status_code == 500
