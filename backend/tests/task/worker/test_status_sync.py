"""
Tests for TaskStatusSync
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from app.models.node import Node, NodeStatus
from app.models.openclaw_task import OpenClawTask
from app.services.openclaw.gateway.dispatch.dispatch_service import DispatchService
from app.services.openclaw.task.worker.status_sync import TaskStatusSync

@pytest.fixture
def mock_dispatch_service():
    service = MagicMock(spec=DispatchService)
    service.dispatch = AsyncMock(return_value={"_dispatched_node_id": "new-node"})
    return service

@pytest.fixture
def status_sync(mock_dispatch_service):
    return TaskStatusSync(mock_dispatch_service)

@pytest.fixture
def mock_db_session():
    session = AsyncMock()
    return session

@pytest.mark.asyncio
async def test_detect_dead_nodes(status_sync, mock_db_session):
    # Setup nodes
    # Node 1: Online but old heartbeat -> Dead
    # Node 2: Online and fresh heartbeat -> Alive
    # Node 3: Offline -> Ignore
    
    old_time = datetime.now() - timedelta(minutes=1)
    fresh_time = datetime.now()
    
    node1 = Node(id="1", status=NodeStatus.ONLINE, last_heartbeat=old_time)
    node2 = Node(id="2", status=NodeStatus.ONLINE, last_heartbeat=fresh_time)
    node3 = Node(id="3", status=NodeStatus.OFFLINE, last_heartbeat=old_time)
    
    # Mock DB query result
    # The query filters for ONLINE and (heartbeat < threshold OR heartbeat is None)
    # So the mock should return [node1]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [node1]
    mock_db_session.execute.return_value = mock_result
    
    dead_nodes = await status_sync._detect_dead_nodes(mock_db_session)
    
    assert len(dead_nodes) == 1
    assert dead_nodes[0].id == "1"
    assert dead_nodes[0].status == NodeStatus.OFFLINE
    mock_db_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_handle_failover(status_sync, mock_db_session, mock_dispatch_service):
    # Setup dead node and task
    dead_node = Node(id="dead-1", status=NodeStatus.OFFLINE)
    
    task = OpenClawTask(
        task_id="t1",
        status="DISPATCHED",
        target_node_id="dead-1",
        parsed_command={"cmd": "run"},
        error_log=""
    )
    
    # Mock DB query for tasks
    mock_tasks_result = MagicMock()
    mock_tasks_result.scalars.return_value.all.return_value = [task]
    
    # Mock DB query for active nodes (for re-dispatch)
    active_node = Node(id="new-node", status=NodeStatus.ONLINE)
    mock_nodes_result = MagicMock()
    mock_nodes_result.scalars.return_value.all.return_value = [active_node]
    
    # Configure db.execute side effects
    # First call: select tasks
    # Second call: select active nodes
    mock_db_session.execute.side_effect = [mock_tasks_result, mock_nodes_result]
    
    await status_sync._handle_failover(mock_db_session, [dead_node])
    
    # Verify task updated
    assert task.status == "DISPATCHED" # It should be re-dispatched
    assert task.target_node_id == "new-node"
    assert "re-dispatched" in task.error_log
    
    # Verify dispatch called
    mock_dispatch_service.dispatch.assert_called_once()
    args = mock_dispatch_service.dispatch.call_args
    assert args[0][0] == {"cmd": "run"} # payload
    assert args[0][1] == "t1" # task_id
    assert args[0][2] == [active_node] # active_nodes

@pytest.mark.asyncio
async def test_handle_failover_no_nodes(status_sync, mock_db_session, mock_dispatch_service):
    dead_node = Node(id="dead-1")
    task = OpenClawTask(task_id="t1", status="DISPATCHED", target_node_id="dead-1", error_log="")
    
    # Mock tasks found
    mock_tasks_result = MagicMock()
    mock_tasks_result.scalars.return_value.all.return_value = [task]
    
    # Mock NO active nodes
    mock_nodes_result = MagicMock()
    mock_nodes_result.scalars.return_value.all.return_value = []
    
    mock_db_session.execute.side_effect = [mock_tasks_result, mock_nodes_result]
    
    await status_sync._handle_failover(mock_db_session, [dead_node])
    
    # Task should be marked FAILED
    assert task.status == "FAILED"
    assert "No active nodes available" in task.error_log
    mock_dispatch_service.dispatch.assert_not_called()
