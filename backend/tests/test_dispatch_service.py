import asyncio
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock, PropertyMock
from datetime import datetime

from app.services.openclaw.gateway.dispatch.dispatch_service import DispatchService
from app.services.openclaw.utils.dispatch.exception import DispatchException, DispatchErrorType
from app.services.openclaw.clients.http.client import OpenClawHttpClient
from app.services.openclaw.node.monitor.node_monitor_service import node_monitor
from app.models.node import NodeStatus

@pytest.fixture
def mock_http_client():
    return AsyncMock(spec=OpenClawHttpClient)

@pytest.fixture
def dispatch_service(mock_http_client):
    return DispatchService(mock_http_client)

@pytest.fixture
def mock_db_session():
    return AsyncMock()

@pytest.fixture
def mock_ws_client():
    # 创建一个模拟的 WS 客户端
    mock = AsyncMock()
    # is_connected 需要是一个 PropertyMock，以便可以被 patch
    type(mock).is_connected = PropertyMock(return_value=True)
    return mock

@pytest.mark.asyncio
async def test_dispatch_ws_success(dispatch_service, mock_db_session):
    """测试 WebSocket 成功下发"""
    task_payload = {"command": "test"}
    task_id = "task_123"
    node_id = "node_123"

    with patch("app.services.openclaw.gateway.dispatch.dispatch_service.AsyncSessionLocal") as mock_session_cls:
        mock_session_cls.return_value.__aenter__.return_value = mock_db_session

        with patch("app.services.openclaw.node.discovery.node_discovery_service.NodeDiscoveryService.get_node_status") as mock_get_status:
            mock_get_status.return_value = {"status": "online"}
            
            # 使用 patch.object 替换整个 client 对象，或者确保 node_monitor.client 是可替换的
            with patch.object(node_monitor, "running", True):
                # 这里我们需要模拟 node_monitor.client.is_connected 和 request
                # 由于 is_connected 是属性，我们直接替换 client 对象比较简单
                mock_client = AsyncMock()
                # 设置 is_connected 为 True
                # 注意：如果 is_connected 是 @property，在 Mock 对象上直接设置属性即可
                mock_client.is_connected = True 
                mock_client.request.return_value = {"status": "success"}
                
                with patch.object(node_monitor, "client", mock_client):
                    res = await dispatch_service.dispatch_to_gateway(task_payload, node_id, task_id)
                    
                    assert res == {"status": "success"}
                    mock_client.request.assert_called_once()

@pytest.mark.asyncio
async def test_dispatch_ws_timeout_http_success(dispatch_service, mock_db_session):
    """测试 WS 超时，回退 HTTP 成功"""
    task_payload = {"command": "test"}
    task_id = "task_123"
    node_id = "node_123"

    with patch("app.services.openclaw.gateway.dispatch.dispatch_service.AsyncSessionLocal") as mock_session_cls:
        mock_session_cls.return_value.__aenter__.return_value = mock_db_session

        with patch("app.services.openclaw.node.discovery.node_discovery_service.NodeDiscoveryService.get_node_status") as mock_get_status:
            mock_get_status.return_value = {"status": "online"}
            
            with patch.object(node_monitor, "running", True):
                mock_client = AsyncMock()
                mock_client.is_connected = True
                mock_client.request.side_effect = asyncio.TimeoutError()
                
                with patch.object(node_monitor, "client", mock_client):
                    # HTTP 成功
                    dispatch_service.http_client.invoke.return_value = {"status": "success"}
                    
                    res = await dispatch_service.dispatch_to_gateway(task_payload, node_id, task_id)
                    
                    assert res == {"status": "success"}
                    dispatch_service.http_client.invoke.assert_called_once()

@pytest.mark.asyncio
async def test_dispatch_node_offline(dispatch_service, mock_db_session):
    """测试节点离线"""
    task_payload = {"command": "test"}
    task_id = "task_123"
    node_id = "node_123"

    with patch("app.services.openclaw.gateway.dispatch.dispatch_service.AsyncSessionLocal") as mock_session_cls:
        mock_session_cls.return_value.__aenter__.return_value = mock_db_session

        with patch("app.services.openclaw.node.discovery.node_discovery_service.NodeDiscoveryService.get_node_status") as mock_get_status:
            mock_get_status.return_value = {"status": "offline"}
            
            with pytest.raises(DispatchException) as exc:
                await dispatch_service.dispatch_to_gateway(task_payload, node_id, task_id)
            
            assert exc.value.error_type == DispatchErrorType.NODE_OFFLINE

@pytest.mark.asyncio
async def test_dispatch_all_failed(dispatch_service, mock_db_session):
    """测试双通道全部失败"""
    task_payload = {"command": "test"}
    task_id = "task_123"
    node_id = "node_123"

    with patch("app.services.openclaw.gateway.dispatch.dispatch_service.AsyncSessionLocal") as mock_session_cls:
        mock_session_cls.return_value.__aenter__.return_value = mock_db_session

        with patch("app.services.openclaw.node.discovery.node_discovery_service.NodeDiscoveryService.get_node_status") as mock_get_status:
            mock_get_status.return_value = {"status": "online"}
            
            with patch.object(node_monitor, "running", True):
                mock_client = AsyncMock()
                mock_client.is_connected = True
                mock_client.request.side_effect = Exception("WS Error")
                
                with patch.object(node_monitor, "client", mock_client):
                    # HTTP 失败 (500)
                    dispatch_service.http_client.invoke.return_value = {"error": "Internal Error", "status": 500}
                    
                    with pytest.raises(DispatchException) as exc:
                        await dispatch_service.dispatch_to_gateway(task_payload, node_id, task_id)
                    
                    assert exc.value.error_type == DispatchErrorType.HTTP_5XX
