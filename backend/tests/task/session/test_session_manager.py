"""
Tests for TaskSessionManager
"""
import pytest
import asyncio
from unittest.mock import MagicMock
from app.models.node import Node
from app.services.openclaw.task.session.session_manager import TaskSessionManager, _SESSION_CACHE

class TestTaskSessionManager:
    
    def setup_method(self):
        _SESSION_CACHE.clear()

    def test_register_and_get_affinity(self):
        sid = "sess-1"
        nid = "node-1"
        TaskSessionManager.register_session(sid, nid, {"version": "1.0"})
        
        affinity = TaskSessionManager.get_affinity_node(sid)
        assert affinity == nid
        assert _SESSION_CACHE[sid]["metadata"]["version"] == "1.0"

    @pytest.mark.asyncio
    async def test_reselect_affinity_node(self):
        sid = "sess-1"
        nid = "node-1"
        TaskSessionManager.register_session(sid, nid, {"version": "1.0"})
        
        # Candidates
        c1 = Node(id="node-1", version="1.0") # Excluded
        c2 = Node(id="node-2", version="1.0") # Good match
        c3 = Node(id="node-3", version="2.0") # Version mismatch
        
        new_node_id = await TaskSessionManager.reselect_affinity_node(sid, nid, [c1, c2, c3])
        
        assert new_node_id == "node-2"
        # Verify cache updated
        assert TaskSessionManager.get_affinity_node(sid) == "node-2"

    @pytest.mark.asyncio
    async def test_reselect_no_candidates(self):
        sid = "sess-1"
        nid = "node-1"
        TaskSessionManager.register_session(sid, nid, {"version": "1.0"})
        
        new_node_id = await TaskSessionManager.reselect_affinity_node(sid, nid, [])
        assert new_node_id is None

    @pytest.mark.asyncio
    async def test_lifecycle_hooks(self):
        # Just ensure no exception
        await TaskSessionManager.on_create("s1", {})
        await TaskSessionManager.on_reuse("s1", "n1")
        await TaskSessionManager.on_destroy("s1")
