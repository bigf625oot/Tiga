import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from app.main import app
from app.services.openclaw.node_manager import NodeManager
from unittest.mock import AsyncMock, patch
from app.models.node import Node, NodeStatus
from datetime import datetime

@pytest.fixture
async def async_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

@pytest.fixture
def mock_node_manager():
    with patch("app.api.endpoints.nodes.node_manager") as mock_manager:
        # Ensure methods are AsyncMocks because endpoints await them
        mock_manager.get_nodes = AsyncMock()
        mock_manager.register_node = AsyncMock()
        mock_manager.heartbeat = AsyncMock()
        mock_manager.check_nodes_health = AsyncMock()
        yield mock_manager

@pytest.mark.asyncio
async def test_list_nodes(async_client, mock_node_manager):
    mock_nodes = [
        Node(id="1", name="node1", status=NodeStatus.ONLINE, platform="linux", last_heartbeat=datetime.now(), created_at=datetime.now()),
        Node(id="2", name="node2", status=NodeStatus.OFFLINE, platform="windows", last_heartbeat=datetime.now(), created_at=datetime.now())
    ]
    mock_node_manager.get_nodes.return_value = mock_nodes
    
    response = await async_client.get("/api/v1/nodes/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "node1"
    assert data[1]["status"] == "offline"

@pytest.mark.asyncio
async def test_register_node(async_client, mock_node_manager):
    new_node_data = {
        "name": "new-node",
        "platform": "docker",
        "ip_address": "10.0.0.5"
    }
    mock_node = Node(id="3", **new_node_data, status=NodeStatus.ONLINE, last_heartbeat=datetime.now(), created_at=datetime.now())
    mock_node_manager.register_node.return_value = mock_node
    
    response = await async_client.post("/api/v1/nodes/register", json=new_node_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "new-node"
    assert data["platform"] == "docker"
    mock_node_manager.register_node.assert_called_once()

@pytest.mark.asyncio
async def test_heartbeat(async_client, mock_node_manager):
    node_id = "test-node-id"
    metrics = {
        "cpu_usage": 45.0,
        "memory_usage": 60.0,
        "disk_usage": 20.0,
        "network_in": 100.0,
        "network_out": 50.0
    }
    mock_node = Node(id=node_id, name="node1", status=NodeStatus.ONLINE, platform="linux", last_heartbeat=datetime.now(), created_at=datetime.now())
    mock_node_manager.heartbeat.return_value = mock_node
    
    response = await async_client.post(f"/api/v1/nodes/{node_id}/heartbeat", json=metrics)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == node_id
    mock_node_manager.heartbeat.assert_called_once()

@pytest.mark.asyncio
async def test_check_health(async_client, mock_node_manager):
    mock_node_manager.check_nodes_health.return_value = None
    response = await async_client.post("/api/v1/nodes/check_health")
    assert response.status_code == 200
    assert response.json() == {"status": "checked"}
    mock_node_manager.check_nodes_health.assert_called_once()
