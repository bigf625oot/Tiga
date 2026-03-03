"""
Tests for Gateway WebSocket Handler and Consistency
"""
import pytest
import asyncio
import time
import json
import zlib
from unittest.mock import MagicMock, AsyncMock, patch
from app.services.openclaw.gateway.gateway.ws_handler import WSConnectionManager, TokenBucket
from app.services.openclaw.gateway.gateway.consistency import ConsistencyManager

class TestTokenBucket:
    def test_consume(self):
        bucket = TokenBucket(10, 100)
        assert bucket.consume(1) is True
        assert bucket.tokens >= 9
        
        bucket.tokens = 0
        assert bucket.consume(1) is False
        
        # Simulate refill
        time.sleep(0.02) # Should refill 2 tokens
        assert bucket.consume(1) is True

class TestWSManager:
    @pytest.mark.asyncio
    async def test_connect_disconnect(self):
        manager = WSConnectionManager()
        ws = AsyncMock()
        await manager.connect(ws, "node-1")
        assert "node-1" in manager.active_connections
        ws.accept.assert_called()
        
        manager.disconnect("node-1")
        assert "node-1" not in manager.active_connections

    @pytest.mark.asyncio
    async def test_message_handling(self):
        manager = WSConnectionManager()
        ws = AsyncMock()
        await manager.connect(ws, "node-1")
        
        # Payload
        payload = {
            "node_id": "node-1",
            "timestamp": time.time(),
            "sequence_id": 1,
            "version": "1.0.0",
            "metrics": {},
            "checksum": 0 # Will fail CRC
        }
        
        # Calculate correct checksum
        metric_str = f"{payload['node_id']}{payload['timestamp']}{payload['sequence_id']}{payload['version']}"
        payload["checksum"] = zlib.crc32(metric_str.encode())
        
        msg = json.dumps(payload)
        
        # Handle
        with patch.object(manager, "_process_payload", new_callable=AsyncMock) as mock_process:
            await manager.handle_message("node-1", msg)
            mock_process.assert_called_with("node-1", payload)
            
        # Test Duplicate
        with patch.object(manager, "_process_payload", new_callable=AsyncMock) as mock_process:
            await manager.handle_message("node-1", msg) # Same sequence
            mock_process.assert_not_called()

    @pytest.mark.asyncio
    async def test_dirty_data_compensation(self):
        manager = WSConnectionManager()
        ws = AsyncMock()
        await manager.connect(ws, "node-1")
        
        # Dirty payload (wrong checksum)
        payload = {
            "node_id": "node-1",
            "timestamp": time.time(),
            "sequence_id": 2,
            "version": "1.0.0",
            "metrics": {},
            "checksum": 999999
        }
        msg = json.dumps(payload)
        
        # Mock consistency manager
        # Since we import consistency_manager inside the method in ws_handler.py,
        # we need to patch it where it is imported FROM, or patch sys.modules?
        # Better: Patch the module attribute in consistency.py and ensure ws_handler uses it.
        # OR: patch("app.services.openclaw.gateway.gateway.consistency.consistency_manager.handle_dirty_data")
        # Let's try patching the class method in ConsistencyManager directly
        
        with patch("app.services.openclaw.gateway.gateway.consistency.ConsistencyManager.handle_dirty_data", new_callable=AsyncMock) as mock_handle:
            await manager.handle_message("node-1", msg)
            mock_handle.assert_called()
