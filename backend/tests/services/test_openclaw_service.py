import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.openclaw.gateway_service import OpenClawService
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
    with patch("app.services.openclaw.gateway_service.OpenClawTools") as MockTools:
        instance = MockTools.return_value
        instance.oc_nodes_async = AsyncMock(return_value=MOCK_NODES_JSON)
        instance.oc_cron_async = AsyncMock(return_value=MOCK_JOBS_JSON)
        instance.oc_plugins_async = AsyncMock(return_value=MOCK_PLUGINS_JSON)
        instance.check_health_async = AsyncMock(return_value={
            "available": True,
            "version": "1.0.0",
            "base_url": "http://test-gateway",
            "tools_enabled": ["cron", "nodes", "plugins"],
            "metrics": {},
            "fallback_enabled": True
        })
        yield instance

@pytest.fixture
def service(mock_tools):
    return OpenClawService()

@pytest.mark.asyncio
async def test_list_nodes(service):
    nodes = await service.list_nodes()
    assert len(nodes) == 1
    assert isinstance(nodes[0], OpenClawNode)
    assert nodes[0].id == "node1"
    assert nodes[0].name == "Test Node"

@pytest.mark.asyncio
async def test_list_activities(service):
    activities = await service.list_activities()
    assert len(activities) == 1
    assert activities[0].id == "job1"
    assert activities[0].type == "crawl"

@pytest.mark.asyncio
async def test_list_plugins(service):
    plugins = await service.list_plugins()
    assert len(plugins) == 1
    assert plugins[0].name == "test-plugin"

@pytest.mark.asyncio
async def test_check_health(service):
    health = await service.check_health()
    assert health.available is True
    assert health.version == "1.0.0"
