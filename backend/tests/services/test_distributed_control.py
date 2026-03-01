import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List
from app.services.openclaw.node_manager import NodeManager
from app.models.node import Node, NodeStatus

@pytest.fixture
def mock_db_session():
    session = AsyncMock()
    # Mock scalars().first() and scalars().all()
    scalars_mock = MagicMock()
    session.execute.return_value = MagicMock()
    session.execute.return_value.scalars.return_value = scalars_mock
    session.add = MagicMock()
    return session

@pytest.fixture
def node_manager():
    # Reset instance
    NodeManager._instance = None
    with patch("app.services.openclaw.node_manager.OpenClawService") as mock_service:
        manager = NodeManager.get_instance()
        manager.openclaw_service = mock_service.return_value
        yield manager

@pytest.mark.asyncio
async def test_update_node_group(node_manager, mock_db_session):
    node_id = "test-node-1"
    existing_node = Node(id=node_id, name="node-1", group="old-group")
    
    # Mock get_node
    mock_db_session.execute.return_value.scalars.return_value.first.return_value = existing_node
    
    updated_node = await node_manager.update_node_group(mock_db_session, node_id, "new-group")
    
    assert updated_node.group == "new-group"
    mock_db_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_update_node_tags(node_manager, mock_db_session):
    node_id = "test-node-1"
    existing_node = Node(id=node_id, name="node-1", tags=[])
    
    # Mock get_node
    mock_db_session.execute.return_value.scalars.return_value.first.return_value = existing_node
    
    tags = ["tag1", "tag2"]
    updated_node = await node_manager.update_node_tags(mock_db_session, node_id, tags)
    
    assert updated_node.tags == tags
    mock_db_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_dispatch_command_by_group(node_manager, mock_db_session):
    # Setup nodes
    node1 = Node(id="1", name="n1", status=NodeStatus.ONLINE, group="group A", tags=[])
    node2 = Node(id="2", name="n2", status=NodeStatus.ONLINE, group="group A", tags=[])
    node3 = Node(id="3", name="n3", status=NodeStatus.ONLINE, group="group B", tags=[])
    
    # Mock DB returning node1 and node2 for group A query
    mock_db_session.execute.return_value.scalars.return_value.all.return_value = [node1, node2]
    
    # Mock node_monitor and ws_client
    with patch("app.services.openclaw.node_monitor.node_monitor") as mock_monitor:
        mock_monitor.running = True
        mock_monitor.client.is_connected = True
        mock_monitor.client.request = AsyncMock(return_value={"status": "ok"})
        
        result = await node_manager.dispatch_command(
            mock_db_session,
            command="test.cmd",
            params={"foo": "bar"},
            target_group="group A"
        )
        
        assert result["status"] == "success"
        assert result["total"] == 2
        assert result["sent"] == 2
        
        # Verify calls
        assert mock_monitor.client.request.call_count == 2
        
        # Verify payload
        calls = mock_monitor.client.request.call_args_list
        # Check first call
        args, kwargs = calls[0]
        assert args[0] == "node.invoke"
        payload = args[1]
        assert payload["command"] == "test.cmd"
        assert payload["params"] == {"foo": "bar"}
        assert payload["nodeId"] in ["1", "2"]

@pytest.mark.asyncio
async def test_dispatch_command_by_tags(node_manager, mock_db_session):
    # Setup nodes
    node1 = Node(id="1", name="n1", status=NodeStatus.ONLINE, tags=["prod", "web"])
    node2 = Node(id="2", name="n2", status=NodeStatus.ONLINE, tags=["prod", "db"])
    node3 = Node(id="3", name="n3", status=NodeStatus.ONLINE, tags=["dev", "web"])
    
    # DB query returns all online nodes first, then we filter in python
    mock_db_session.execute.return_value.scalars.return_value.all.return_value = [node1, node2, node3]
    
    # Mock node_monitor
    with patch("app.services.openclaw.node_monitor.node_monitor") as mock_monitor:
        mock_monitor.running = True
        mock_monitor.client.is_connected = True
        mock_monitor.client.request = AsyncMock(return_value={"status": "ok"})
        
        # Filter by tags=["prod"]
        result = await node_manager.dispatch_command(
            mock_db_session,
            command="test.cmd",
            params={},
            target_tags=["prod"]
        )
        
        assert result["total"] == 2 # node1 and node2
        assert result["sent"] == 2
        
        # Filter by tags=["prod", "web"]
        mock_monitor.client.request.reset_mock()
        result = await node_manager.dispatch_command(
            mock_db_session,
            command="test.cmd",
            params={},
            target_tags=["prod", "web"]
        )
        
        assert result["total"] == 1 # only node1 matches both
        assert result["sent"] == 1
        
