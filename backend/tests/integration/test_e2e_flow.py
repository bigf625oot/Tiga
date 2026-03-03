"""
End-to-End Integration Test for OpenClaw Distributed Execution

Tests the full flow:
1. Node Registration & Heartbeat (High-Frequency)
2. Task Creation & Parsing (with Memory Recall)
3. Task Dispatch (Sharding & Session Affinity)
4. Status Sync & Consistency Check
"""

import pytest
import asyncio
import time
import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock, patch

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.node import Node, NodeStatus
from app.models.openclaw_task import OpenClawTask
from app.services.openclaw.node.monitor.heartbeat import HeartbeatMonitor
from app.services.openclaw.gateway.gateway.ws_handler import WSConnectionManager
from app.services.openclaw.gateway.dispatch.dispatch_service import DispatchService
from app.services.openclaw.task.session.session_manager import TaskSessionManager
from app.services.openclaw.task.memory.storage import RedisMemoryStorage
from app.services.openclaw.task.parser.task_parser_service import parse_task_intent

# Mock DB Session
@pytest.fixture
def mock_db_session():
    session = AsyncMock(spec=AsyncSession)
    return session

@pytest.fixture
def ws_manager():
    return WSConnectionManager()

@pytest.fixture
def heartbeat_monitor():
    return HeartbeatMonitor("node-test-1", "ws://gateway")

@pytest.mark.asyncio
async def test_full_execution_flow(mock_db_session, ws_manager, heartbeat_monitor):
    """
    Scenario:
    1. Node 'node-test-1' connects and sends heartbeats.
    2. User sends prompt "Check server status every 5 min".
    3. Parser parses intent, recalling context.
    4. Task is created and dispatched to 'node-test-1' (Session Affinity).
    5. Node executes and updates status.
    6. Gateway validates consistency.
    """
    
    # --- Step 1: Node Registration & Heartbeat ---
    print("\n[Step 1] Node Heartbeat")
    ws_mock = AsyncMock()
    await ws_manager.connect(ws_mock, "node-test-1")
    
    # Simulate Heartbeat Payload
    metrics = heartbeat_monitor._collect_metrics()
    hb_payload = {
        "node_id": "node-test-1",
        "timestamp": time.time(),
        "sequence_id": 1,
        "version": "1.0.0",
        "metrics": metrics,
        "checksum": 0 # We mock validation so 0 is fine if we patch
    }
    # Mock consistency check to pass
    with patch.object(ws_manager, "_check_consistency", return_value=True):
        await ws_manager.handle_message("node-test-1", json.dumps(hb_payload))
    
    assert "node-test-1" in ws_manager.active_connections
    assert "node-test-1" in ws_manager.heartbeat_tracker
    
    # --- Step 2: Task Parsing with Memory ---
    print("[Step 2] Task Parsing")
    # Mock Memory Storage
    with patch("app.services.openclaw.task.parser.task_parser_service.get_memory_storage") as mock_get_storage:
        mock_storage = AsyncMock()
        mock_storage._index_created = True
        mock_storage.get_session_context.return_value = []
        mock_storage.search_memory.return_value = []
        mock_get_storage.return_value = mock_storage
        
        # Mock LLM Call
        with patch("app.services.openclaw.task.parser.task_parser_service._call_llm", return_value='{"command": "check_status", "schedule": "*/5 * * * *"}'):
            with patch("app.services.openclaw.task.parser.task_parser_service._get_active_llm", return_value=("key", "url", "model")):
                 task_data = await parse_task_intent("Check server status", mock_db_session, session_id="sess-1")
    
    assert task_data["command"] == "check_status"
    
    # --- Step 3: Dispatch & Session Affinity ---
    print("[Step 3] Dispatch")
    # Setup Dispatch Service
    dispatch_service = DispatchService(http_client=AsyncMock(), selector=MagicMock())
    dispatch_service.selector.select.return_value = Node(id="node-test-1", status=NodeStatus.ONLINE, version="1.0.0")
    dispatch_service.dispatch_to_gateway = AsyncMock(return_value={"status": "ok"})
    
    active_nodes = [Node(id="node-test-1", status=NodeStatus.ONLINE, version="1.0.0")]
    
    # Dispatch with Session
    task_payload = {"cmd": task_data["command"], "session_id": "sess-1"}
    result = await dispatch_service.dispatch(task_payload, "task-1", active_nodes)
    
    assert result["_dispatched_node_id"] == "node-test-1"
    # Verify Session Created
    affinity = TaskSessionManager.get_affinity_node("sess-1")
    assert affinity == "node-test-1"
    
    # --- Step 4: Consistency Check & Compensation ---
    print("[Step 4] Consistency Check (Simulate Dirty Data)")
    # Send bad payload
    bad_payload = hb_payload.copy()
    bad_payload["checksum"] = 999999 # Invalid
    
    # Since the previous attempts to patch handle_dirty_data failed to be detected (even though we see log output?),
    # maybe we should inspect the audit log in consistency_manager instead of checking the mock call.
    # The real handle_dirty_data writes to self.audit_log.

    # Let's use the real ConsistencyManager and check its state!
    # We still need to patch WSManager._check_consistency to force it to fail.

    from app.services.openclaw.gateway.gateway.consistency import consistency_manager as real_cm

    # Clear log first
    real_cm.audit_log.clear()

    # We need to mock the DB session inside handle_dirty_data, otherwise it will try to connect to real DB.
    # handle_dirty_data uses AsyncSessionLocal().
    # We can patch 'app.services.openclaw.gateway.gateway.consistency.AsyncSessionLocal'

    mock_session_ctx = MagicMock()
    mock_session_ctx.__aenter__.return_value = mock_db_session
    mock_session_ctx.__aexit__.return_value = None

    with patch("app.services.openclaw.gateway.gateway.consistency.AsyncSessionLocal", return_value=mock_session_ctx):
        # Also need to patch ws_manager.active_connections to avoid sending real WS message in handle_dirty_data
        # (though we are using mocks for WS anyway)

        # Mock send_json on the connection
        mock_ws_conn = ws_manager.active_connections["node-test-1"]
        # It's an AsyncMock from Step 1

        # Force consistency check fail
        with patch.object(ws_manager, "_check_consistency", return_value=False):
            # Increase sequence_id to avoid deduplication
            bad_payload["sequence_id"] = 2
            
            # We need to make sure consistency_manager uses OUR ws_manager instance
            # Patch the ws_handler module's ws_manager attribute which is imported by consistency.py
            # consistency.py: from .ws_handler import ws_manager
            
            # Since consistency.py imports ws_manager from .ws_handler, we should patch
            # app.services.openclaw.gateway.gateway.ws_handler.ws_manager
            # AND make sure consistency module sees it?
            
            # If consistency module has already imported it, patching ws_handler.ws_manager won't affect
            # the reference already held by consistency module.
            
            # So we must patch `app.services.openclaw.gateway.gateway.consistency.ws_manager`.
            # BUT the error says `consistency` module does not have attribute `ws_manager`.
            # This means it is NOT in the module namespace.
            # It must be imported inside a function/method in consistency.py.
            
            # Let's check consistency.py content.
            # In handle_dirty_data:
            # from .ws_handler import ws_manager
            
            # Ah! It is a local import inside handle_dirty_data method!
            
            # So we CANNOT patch it on the consistency module.
            # We MUST patch it on the `ws_handler` module, because `from .ws_handler import ws_manager`
            # will look up `ws_manager` in `ws_handler` module.
            
            with patch("app.services.openclaw.gateway.gateway.ws_handler.ws_manager", ws_manager):
                await ws_manager.handle_message("node-test-1", json.dumps(bad_payload))

                # Check side effects instead of mock call
                assert len(real_cm.audit_log) > 0
                assert real_cm.audit_log[-1]["node_id"] == "node-test-1"
                assert real_cm.audit_log[-1]["reason"] == "checksum_mismatch"
                
                # Check DB update was called
                assert mock_db_session.execute.called
                
            # Check force_sync command sent
            mock_ws_conn.send_json.assert_called()
            args = mock_ws_conn.send_json.call_args[0][0]
            assert args["action"] == "force_sync"
             
    print("Integration Test Completed Successfully")

if __name__ == "__main__":
    # Allow running directly
    asyncio.run(test_full_execution_flow(AsyncMock(), WSConnectionManager(), HeartbeatMonitor("n1", "u")))
