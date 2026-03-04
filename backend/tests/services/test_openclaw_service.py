import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.openclaw.gateway.service import OpenClawService
from app.schemas.openclaw import OpenClawNode

MOCK_NODES_JSON = json.dumps({
    "nodes": [
        {"id": "node1", "name": "Test Node", "status": "active", "platform": "linux", "version": "1.0.0", "address": "127.0.0.1"}
    ]
})

MOCK_JOBS_JSON = json.dumps({
    "jobs": [
        {"id": "job1", "command": "crawl http://example.com", "enabled": True, "schedule": "0 * * * *", "lastRun": "2023-01-01", "nextRun": "2023-01-02"}
    ]
})

MOCK_PLUGINS_JSON = json.dumps({
    "plugins": [
        {"name": "test-plugin", "version": "1.0.0", "status": "active", "description": "A test plugin"}
    ]
})

@pytest.fixture
def mock_tools():
    with patch("app.services.openclaw.gateway.service.OpenClawTools") as MockTools:
        instance = MockTools.return_value
        instance.oc_nodes_async = AsyncMock(return_value=MOCK_NODES_JSON)
        instance.oc_cron_async = AsyncMock(return_value=MOCK_JOBS_JSON)
        instance.oc_plugins_async = AsyncMock(return_value=MOCK_PLUGINS_JSON)
        # Mock client connection for health check
        instance.client = MagicMock()
        instance.client.is_connected = True
        
        yield instance

@pytest.fixture
def service(mock_tools):
    svc = OpenClawService()
    # Ensure tools is our mock
    svc.tools = mock_tools
    return svc

@pytest.mark.asyncio
async def test_check_health(service):
    # The new implementation checks ws client status
    health = await service.check_health()
    assert health.available is True
    assert health.version == "connected (ws)"
