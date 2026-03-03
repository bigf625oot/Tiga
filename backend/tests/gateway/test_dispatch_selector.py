"""
Integration tests for DispatchService selector logic
"""
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from app.models.node import Node, NodeStatus
from app.services.openclaw.gateway.dispatch.dispatch_service import DispatchService, MonitorMetricsAdapter
from app.services.openclaw.node.selector import TagSelector, LeastLoadSelector
from app.services.openclaw.utils.dispatch.exception import DispatchException, DispatchErrorType

@pytest.fixture
def mock_http_client():
    client = MagicMock()
    client.invoke = AsyncMock(return_value={"status": 200})
    return client

@pytest.fixture
def dispatch_service(mock_http_client):
    return DispatchService(http_client=mock_http_client)

@pytest.mark.asyncio
async def test_dispatch_tag_selector(mock_http_client):
    # Setup nodes
    node1 = Node(id="gpu-1", name="gpu-node", status=NodeStatus.ONLINE, tags={"type": "gpu"})
    node2 = Node(id="cpu-1", name="cpu-node", status=NodeStatus.ONLINE, tags={"type": "cpu"})
    active_nodes = [node1, node2]
    
    # Initialize service with TagSelector
    selector = TagSelector(tags={"type": "gpu"})
    service = DispatchService(http_client=mock_http_client, selector=selector)
    
    # Mock dispatch_to_gateway to avoid actual network/DB calls
    service.dispatch_to_gateway = AsyncMock(return_value={"status": "ok"})
    
    # Execute dispatch
    task_payload = {"cmd": "run"}
    await service.dispatch(task_payload, "task-1", active_nodes)
    
    # Verify correct node selected
    service.dispatch_to_gateway.assert_called_once_with(task_payload, "gpu-1", "task-1")

@pytest.mark.asyncio
async def test_dispatch_least_load_selector(mock_http_client):
    # Setup nodes
    node1 = Node(id="node-1", name="node-1", status=NodeStatus.ONLINE)
    node2 = Node(id="node-2", name="node-2", status=NodeStatus.ONLINE)
    active_nodes = [node1, node2]
    
    # Mock Metrics via node_monitor patch
    # We need to patch the actual source of node_monitor, since dispatch_service imports it locally
    with patch("app.services.openclaw.node.monitor.node_monitor_service.node_monitor") as mock_monitor:
        # node-1 load: 100ms/10 = 10ms
        # node-2 load: 50ms/10 = 5ms -> Should pick node-2
        mock_monitor.stats = {
            "node-1": {"pings": 10, "total_rtt": 100},
            "node-2": {"pings": 10, "total_rtt": 50}
        }
        
        # Initialize service with LeastLoadSelector (using default adapter which uses patched node_monitor)
        # Note: DispatchService defaults to LeastLoadSelector if POLICY is 'least_load' (default)
        # But we want to ensure we use the one with our adapter (which imports node_monitor)
        # The adapter in dispatch_service.py imports node_monitor from module scope.
        # Patching it where it is imported (in dispatch_service) is correct.
        
        service = DispatchService(http_client=mock_http_client)
        # Ensure it's using LeastLoadSelector
        assert isinstance(service.selector, LeastLoadSelector)
        
        # Mock dispatch_to_gateway
        service.dispatch_to_gateway = AsyncMock(return_value={"status": "ok"})
        
        # Execute dispatch
        await service.dispatch({"cmd": "run"}, "task-2", active_nodes)
        
        # Verify node-2 selected (lower load)
        service.dispatch_to_gateway.assert_called_once_with({"cmd": "run"}, "node-2", "task-2")

@pytest.mark.asyncio
async def test_dispatch_no_suitable_node(mock_http_client):
    node1 = Node(id="1", status=NodeStatus.OFFLINE)
    active_nodes = [node1]
    
    service = DispatchService(http_client=mock_http_client) # Defaults to LeastLoadSelector
    
    # Dispatch should fail
    with pytest.raises(DispatchException) as excinfo:
        await service.dispatch({"cmd": "run"}, "task-3", active_nodes)
    
    assert excinfo.value.error_type == DispatchErrorType.NODE_OFFLINE
