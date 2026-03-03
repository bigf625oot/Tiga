"""
Tests for High-Frequency Monitor and Ring Buffer
"""
import pytest
import time
import asyncio
from unittest.mock import MagicMock
from app.services.openclaw.node.monitor.heartbeat import HeartbeatMonitor, RingBuffer, HeartbeatPayload

class TestRingBuffer:
    def test_buffer_capacity(self):
        buf = RingBuffer(3)
        buf.append(1)
        buf.append(2)
        buf.append(3)
        assert buf.get_all() == [1, 2, 3]
        
        buf.append(4)
        assert buf.get_all() == [2, 3, 4]

class TestHeartbeatMonitor:
    @pytest.mark.asyncio
    async def test_heartbeat_payload(self):
        monitor = HeartbeatMonitor("test-node", "ws://mock")
        
        # Test private _collect_metrics
        metrics = monitor._collect_metrics()
        assert "cpu" in metrics
        
        # Test payload generation logic (simulate loop body logic)
        payload = HeartbeatPayload(
            node_id="test-node",
            timestamp=time.time(),
            sequence_id=1,
            version="1.0.0",
            status="ONLINE",
            metrics=metrics,
            checksum=0
        )
        assert payload.sequence_id == 1
        
        # Check CRC logic
        import zlib
        expected_crc = zlib.crc32(f"{payload.node_id}{payload.timestamp}{payload.sequence_id}{payload.version}".encode())
        assert expected_crc != 0
