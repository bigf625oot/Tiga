import sys
from unittest.mock import MagicMock, patch

# Mock brave and trafilatura modules BEFORE importing app code
sys.modules["brave"] = MagicMock()
sys.modules["trafilatura"] = MagicMock()
sys.modules["trafilatura.meta"] = MagicMock()
sys.modules["trafilatura.spider"] = MagicMock()

import json
import pytest
from app.services.openclaw.agent_tools import OpenClawTools

@pytest.fixture
def openclaw_tools():
    return OpenClawTools(base_url="http://mock-gateway", token="mock-token")

@patch("app.services.openclaw.api_client.httpx.AsyncClient.post")
@pytest.mark.asyncio
async def test_oc_web_search(mock_post, openclaw_tools):
    # Mock successful response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": ["test"]}
    mock_post.return_value = mock_response

    result_json = await openclaw_tools.oc_web_search_async("test query", count=3)
    result = json.loads(result_json)
    
    # Verify request
    mock_post.assert_called()
    args, kwargs = mock_post.call_args
    assert kwargs["json"] == {"tool": "web_search", "params": {"query": "test query", "count": 3}}
    assert kwargs["headers"]["Authorization"] == "Bearer mock-token"
    
    # Verify result
    assert "results" in result

@patch("app.services.openclaw.api_client.httpx.AsyncClient.post")
@pytest.mark.asyncio
async def test_oc_cron(mock_post, openclaw_tools):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"jobs": []}
    mock_post.return_value = mock_response

    result_json = await openclaw_tools.oc_cron_async(action="list")
    result = json.loads(result_json)
    
    mock_post.assert_called()
    args, kwargs = mock_post.call_args
    assert kwargs["json"] == {"tool": "cron", "params": {"action": "list"}}
    assert "jobs" in result

@patch("app.services.openclaw.api_client.httpx.AsyncClient.post")
@pytest.mark.asyncio
async def test_oc_nodes(mock_post, openclaw_tools):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"nodes": []}
    mock_post.return_value = mock_response

    # oc_nodes is dynamically created, call it directly
    func = getattr(openclaw_tools, "_dyn_nodes")
    result_json = await func(action="list")
    result = json.loads(result_json)
    
    mock_post.assert_called()
    args, kwargs = mock_post.call_args
    assert kwargs["json"] == {"tool": "nodes", "params": {"action": "list"}}
    assert "nodes" in result

@patch("app.services.openclaw.api_client.httpx.AsyncClient.post")
@pytest.mark.asyncio
async def test_fallback_web_search(mock_post, openclaw_tools):
    # Mock failure
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_post.return_value = mock_response

    # 在测试中模拟 BRAVE_AVAILABLE 为 True
    with patch("app.services.openclaw.agent_tools.BRAVE_AVAILABLE", True):
        # 模拟 BraveSearchTools 类
        mock_brave_cls = MagicMock()
        mock_brave_instance = mock_brave_cls.return_value
        mock_brave_instance.brave_search.return_value = '{"web_results": []}'
        
        # 将模拟类注入到 openclaw.agent_tools 模块中
        with patch.object(sys.modules["app.services.openclaw.agent_tools"], "BraveSearchTools", mock_brave_cls, create=True):
            result_json = await openclaw_tools.oc_web_search_async("fallback query")
            result = json.loads(result_json)
            
            mock_brave_cls.assert_called()
            mock_brave_instance.brave_search.assert_called_with(query="fallback query", max_results=5)
            assert result["source"] == "brave_fallback"
