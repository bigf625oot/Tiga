import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from app.services.openclaw.node_manager import NodeManager
from app.models.node import Node, NodeStatus, NodeMetric, Alert, AlertLevel
from app.schemas.node import NodeCreate, NodeMetricCreate

@pytest.fixture
def mock_db_session():
    session = AsyncMock()
    # Ensure nested mocks are also AsyncMocks or MagicMocks as needed
    # scalars() returns a sync mock that returns another mock
    scalars_mock = MagicMock()
    session.execute.return_value = MagicMock()
    session.execute.return_value.scalars.return_value = scalars_mock
    # db.add is synchronous
    session.add = MagicMock()
    return session

@pytest.fixture
def node_manager():
    # Reset instance to ensure fresh state
    NodeManager._instance = None
    with patch("app.services.openclaw.node_manager.OpenClawService") as mock_service:
        manager = NodeManager.get_instance()
        manager.openclaw_service = mock_service.return_value
        yield manager

@pytest.mark.asyncio
async def test_register_node(node_manager, mock_db_session):
    node_in = NodeCreate(name="test-node", platform="linux", ip_address="192.168.1.1")
    
    # Mock existing node check (return None)
    # Configure mock for the first execute call (duplicate check)
    mock_db_session.execute.return_value.scalars.return_value.first.return_value = None
    
    node = await node_manager.register_node(mock_db_session, node_in)
    
    assert node.name == "test-node"
    assert node.platform == "linux"
    assert node.status == NodeStatus.ONLINE
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_heartbeat_existing_node(node_manager, mock_db_session):
    node_id = "test-id"
    existing_node = Node(id=node_id, name="test-node", status=NodeStatus.OFFLINE)
    
    # Mock get_node returning existing_node
    mock_db_session.execute.return_value.scalars.return_value.first.return_value = existing_node
    
    metrics = NodeMetricCreate(
        cpu_usage=50.0,
        memory_usage=60.0,
        disk_usage=70.0,
        network_in=100.0,
        network_out=200.0
    )
    
    updated_node = await node_manager.heartbeat(mock_db_session, node_id, metrics)
    
    assert updated_node.status == NodeStatus.ONLINE
    assert updated_node.last_heartbeat is not None
    # Check metrics added
    mock_db_session.add.assert_called() # Should add metric
    args, _ = mock_db_session.add.call_args
    assert isinstance(args[0], NodeMetric)
    assert args[0].cpu_usage == 50.0

@pytest.mark.asyncio
async def test_alert_generation(node_manager, mock_db_session):
    node_id = "test-id"
    existing_node = Node(id=node_id, name="test-node", status=NodeStatus.ONLINE)
    mock_db_session.execute.return_value.scalars.return_value.first.return_value = existing_node
    
    # High CPU to trigger alert
    metrics = NodeMetricCreate(
        cpu_usage=95.0,
        memory_usage=60.0,
        disk_usage=70.0,
        network_in=100.0,
        network_out=200.0
    )
    
    # Mock alert check (no existing alert)
    # We need to handle multiple calls to execute: 1. get_node, 2. check existing alert
    
    # Simulating execute results is complex with AsyncMock side_effects for coroutines
    # Simplified approach: Check if create_alert calls add
    
    # Mock _check_metrics_for_alerts behavior or test logic inside it
    # Let's rely on heartbeat calling _check_metrics_for_alerts
    
    # We need to mock the alert check query to return None (no existing active alert)
    def execute_side_effect(stmt):
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None # No existing alert
        # If looking for node, return node
        if "FROM nodes" in str(stmt):
             mock_result.scalars.return_value.first.return_value = existing_node
        return mock_result

    mock_db_session.execute.side_effect = execute_side_effect
    
    await node_manager.heartbeat(mock_db_session, node_id, metrics)
    
    # Verify alert added
    # add is called twice: 1 for metric, 1 for alert
    assert mock_db_session.add.call_count >= 2 
    
    # Find the alert object in calls
    alert_added = False
    for call in mock_db_session.add.call_args_list:
        obj = call[0][0]
        if isinstance(obj, Alert):
            if obj.level == AlertLevel.P1 and "High CPU" in obj.message:
                alert_added = True
    assert alert_added

@pytest.mark.asyncio
async def test_check_nodes_health(node_manager, mock_db_session):
    # Setup: One healthy node, one stale node
    healthy_node = Node(id="1", name="healthy", status=NodeStatus.ONLINE, last_heartbeat=datetime.now())
    stale_node = Node(id="2", name="stale", status=NodeStatus.ONLINE, last_heartbeat=datetime.now() - timedelta(seconds=60))
    
    # Mock return values for different calls
    mock_scalars = mock_db_session.execute.return_value.scalars.return_value
    
    # First call: nodes check -> returns [stale_node]
    # Second call: subtasks -> returns []
    # But wait, check_nodes_health calls execute(select(Node)...) first.
    # Then it loops. Inside loop:
    #   create_alert -> execute(select(Alert)...)
    #   execute(select(SubTask)...)
    
    # So sequence of execute().scalars() calls:
    # 1. Node check (.all())
    # 2. Alert check (.first())
    # 3. SubTask check (.all())
    
    # We need to configure the mock to handle this sequence
    
    # Reset the mock_db_session execution first to clear previous calls from other tests if any (though fixture resets it)
    
    # We can use side_effect on the scalars_mock directly if we want to distinguish .all() vs .first()
    # But .scalars() returns the same mock object.
    
    # Let's just set the return values on the methods
    mock_scalars.all.side_effect = [[stale_node], []]
    mock_scalars.first.return_value = None
    
    await node_manager.check_nodes_health(mock_db_session)
    
    assert stale_node.status == NodeStatus.OFFLINE
    # Alert should be created
    mock_db_session.add.assert_called()
    args, _ = mock_db_session.add.call_args
    assert isinstance(args[0], Alert)
    assert args[0].level == AlertLevel.P0
