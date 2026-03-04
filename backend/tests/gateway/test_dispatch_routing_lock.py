import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.services.openclaw.common.errors import DispatchException, DispatchErrorType
from app.services.openclaw.gateway.dispatch import DispatchService
from app.services.openclaw.gateway.routing_lock import ROUTING_META_FIELD, ROUTING_TARGET_FIELD, verify_routing_payload


@pytest.mark.asyncio
async def test_dispatch_routing_lock_normal_payload_field_hits_selected_node():
    service = DispatchService()
    selected_node = str(uuid.uuid4())
    payload = {"command": "echo ok", "node_id": selected_node}

    with patch("app.services.openclaw.gateway.dispatch.AsyncSessionLocal") as session_cls, patch(
        "app.services.openclaw.gateway.dispatch.NodeDiscoveryService.get_node_status",
        new_callable=AsyncMock,
    ) as get_node_status, patch("app.services.openclaw.node.monitor.node_monitor") as mock_monitor:
        session_cls.return_value.__aenter__.return_value = AsyncMock()
        get_node_status.return_value = {"status": "online"}
        mock_monitor.running = True
        mock_monitor.client.is_connected = True
        mock_monitor.client.request = AsyncMock(return_value={"ok": True})

        res = await service.dispatch_to_gateway(payload, selected_node, "task-normal")

        assert res == {"ok": True}
        sent_payload = mock_monitor.client.request.call_args.args[1]
        assert sent_payload[ROUTING_TARGET_FIELD] == selected_node
        assert sent_payload[ROUTING_META_FIELD]["source"] == "payload"
        assert verify_routing_payload(sent_payload, expected_node_id=selected_node) == selected_node


@pytest.mark.asyncio
async def test_dispatch_routing_lock_tampered_payload_rejected():
    service = DispatchService()
    selected_node = str(uuid.uuid4())
    payload = {"command": "echo bad", "node_id": str(uuid.uuid4())}

    with patch("app.services.openclaw.gateway.dispatch.AsyncSessionLocal") as session_cls, patch(
        "app.services.openclaw.gateway.dispatch.NodeDiscoveryService.get_node_status",
        new_callable=AsyncMock,
    ) as get_node_status, patch("app.services.openclaw.node.monitor.node_monitor") as mock_monitor:
        session_cls.return_value.__aenter__.return_value = AsyncMock()
        get_node_status.return_value = {"status": "online"}
        mock_monitor.running = True
        mock_monitor.client.is_connected = True
        mock_monitor.client.request = AsyncMock(return_value={"ok": True})

        with pytest.raises(DispatchException) as exc:
            await service.dispatch_to_gateway(payload, selected_node, "task-tampered")

        assert exc.value.error_type == DispatchErrorType.ROUTING_FORBIDDEN
        assert exc.value.http_status == 403
        assert exc.value.error_code == "OPENCLAW_ROUTING_TARGET_MISMATCH"
        mock_monitor.client.request.assert_not_called()


@pytest.mark.asyncio
async def test_dispatch_routing_lock_gateway_injects_target_when_missing():
    service = DispatchService()
    selected_node = str(uuid.uuid4())
    payload = {"command": "echo inject"}

    with patch("app.services.openclaw.gateway.dispatch.AsyncSessionLocal") as session_cls, patch(
        "app.services.openclaw.gateway.dispatch.NodeDiscoveryService.get_node_status",
        new_callable=AsyncMock,
    ) as get_node_status, patch("app.services.openclaw.node.monitor.node_monitor") as mock_monitor:
        session_cls.return_value.__aenter__.return_value = AsyncMock()
        get_node_status.return_value = {"status": "online"}
        mock_monitor.running = True
        mock_monitor.client.is_connected = True
        mock_monitor.client.request = AsyncMock(return_value={"ok": True})

        await service.dispatch_to_gateway(payload, selected_node, "task-inject")

        sent_payload = mock_monitor.client.request.call_args.args[1]
        assert sent_payload[ROUTING_TARGET_FIELD] == selected_node
        assert sent_payload[ROUTING_META_FIELD]["source"] == "gateway"
        assert verify_routing_payload(sent_payload, expected_node_id=selected_node) == selected_node
