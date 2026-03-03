"""
Tests for TaskSharder
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.models.node import Node
from app.services.openclaw.gateway.dispatch.dispatch_service import DispatchService
from app.services.openclaw.gateway.dispatch.sharding import TaskSharder, ShardingStrategy

@pytest.fixture
def dispatch_service():
    service = MagicMock(spec=DispatchService)
    # Mock dispatch_to_gateway to return success
    service.dispatch_to_gateway = AsyncMock(return_value={"status": "ok"})
    return service

@pytest.fixture
def sharder(dispatch_service):
    return TaskSharder(dispatch_service)

@pytest.fixture
def nodes():
    return [
        Node(id="node-1", name="n1"),
        Node(id="node-2", name="n2")
    ]

@pytest.mark.asyncio
async def test_shard_broadcast(sharder, dispatch_service, nodes):
    payload = {"cmd": "test"}
    result = await sharder.shard_and_dispatch("t1", payload, nodes, strategy=ShardingStrategy.BROADCAST)
    
    assert result["success"] == 2
    assert dispatch_service.dispatch_to_gateway.call_count == 2
    # Check calls
    dispatch_service.dispatch_to_gateway.assert_any_call(payload, "node-1", "t1")
    dispatch_service.dispatch_to_gateway.assert_any_call(payload, "node-2", "t1")

@pytest.mark.asyncio
async def test_shard_round_robin(sharder, dispatch_service, nodes):
    payloads = [{"cmd": "p1"}, {"cmd": "p2"}, {"cmd": "p3"}]
    result = await sharder.shard_and_dispatch("t2", payloads, nodes, strategy=ShardingStrategy.ROUND_ROBIN)
    
    assert result["success"] == 3
    assert dispatch_service.dispatch_to_gateway.call_count == 3
    # p1 -> n1, p2 -> n2, p3 -> n1
    dispatch_service.dispatch_to_gateway.assert_any_call({"cmd": "p1"}, "node-1", "t2")
    dispatch_service.dispatch_to_gateway.assert_any_call({"cmd": "p2"}, "node-2", "t2")
    dispatch_service.dispatch_to_gateway.assert_any_call({"cmd": "p3"}, "node-1", "t2")

@pytest.mark.asyncio
async def test_shard_targeted(sharder, dispatch_service, nodes):
    payloads = [
        {"cmd": "p1", "target_node_id": "node-2"},
        {"cmd": "p2", "target_node_id": "node-1"}
    ]
    result = await sharder.shard_and_dispatch("t3", payloads, nodes, strategy=ShardingStrategy.TARGETED)
    
    assert result["success"] == 2
    dispatch_service.dispatch_to_gateway.assert_any_call(payloads[0], "node-2", "t3")
    dispatch_service.dispatch_to_gateway.assert_any_call(payloads[1], "node-1", "t3")

@pytest.mark.asyncio
async def test_shard_targeted_fallback(sharder, dispatch_service, nodes):
    # No target_node_id, should fallback to RR (or linear assignment logic implemented)
    payloads = [{"cmd": "p1"}]
    result = await sharder.shard_and_dispatch("t4", payloads, nodes, strategy=ShardingStrategy.TARGETED)
    
    assert result["success"] == 1
    # Should assign to node-1 (first node)
    dispatch_service.dispatch_to_gateway.assert_any_call(payloads[0], "node-1", "t4")

@pytest.mark.asyncio
async def test_shard_no_nodes(sharder):
    result = await sharder.shard_and_dispatch("t5", {}, [], strategy=ShardingStrategy.BROADCAST)
    assert result["status"] == "failed"
