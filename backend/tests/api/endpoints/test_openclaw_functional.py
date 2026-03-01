import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.api.deps import get_db
from app.api.endpoints.openclaw import get_service
from app.schemas.openclaw import OpenClawNode, OpenClawActivity, OpenClawPlugin, OpenClawHealth

# Create a client
client = TestClient(app)

@pytest.fixture
def mock_service():
    mock_svc = MagicMock()
    
    # Mock health
    mock_svc.check_health = AsyncMock(return_value=OpenClawHealth(
        available=True,
        version="1.0.0",
        base_url="http://test-gateway",
        tools_enabled=["cron", "nodes", "plugins"],
        metrics={},
        fallback_enabled=True
    ))
    
    # Mock nodes
    mock_svc.list_nodes = AsyncMock(return_value=[
        OpenClawNode(id="node1", name="Test Node", status="active", platform="linux", version="1.0.0", address="127.0.0.1")
    ])
    
    # Mock activities
    mock_svc.list_activities = AsyncMock(return_value=[
        OpenClawActivity(id="job1", name="Test Job", type="crawl", status="active", description="crawl http://example.com")
    ])
    
    # Mock plugins
    mock_svc.list_plugins = AsyncMock(return_value=[
        OpenClawPlugin(name="test-plugin", version="1.0.0", status="active", description="A test plugin")
    ])
    
    # Mock create_task
    mock_svc.create_task = AsyncMock(return_value={
        "status": "success",
        "task": {"name": "Test Task", "schedule": "0 9 * * *", "command": "crawl http://test.com", "id": "task_123"}
    })

    app.dependency_overrides[get_service] = lambda: mock_svc
    yield mock_svc
    del app.dependency_overrides[get_service]

def test_health_check(mock_service):
    response = client.get("/api/v1/openclaw/health")
    assert response.status_code == 200
    data = response.json()
    assert data["available"] is True
    assert data["version"] == "1.0.0"

def test_list_nodes(mock_service):
    response = client.get("/api/v1/openclaw/nodes")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "node1"
    assert data[0]["name"] == "Test Node"

def test_list_activities(mock_service):
    response = client.get("/api/v1/openclaw/activities")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "job1"
    assert data[0]["type"] == "crawl"

def test_list_plugins(mock_service):
    response = client.get("/api/v1/openclaw/plugins")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "test-plugin"

def test_create_task(mock_service):
    async def mock_get_db():
        yield MagicMock()
    
    app.dependency_overrides[get_db] = mock_get_db
    
    response = client.post(
        "/api/v1/openclaw/create_task", 
        json={"prompt": "crawl google every day"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "task" in data
    assert data["task"]["command"] == "crawl http://test.com"
    
    # Cleanup
    del app.dependency_overrides[get_db]
