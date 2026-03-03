import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from app.services.openclaw.gateway.gateway.gateway_service import OpenClawService
from app.services.openclaw.node.manager.node_manager_service import NodeManager

@pytest.fixture
def mock_db_session():
    return AsyncMock()

@pytest.mark.asyncio
async def test_integration_gateway_and_node_manager(mock_db_session):
    """
    集成测试：验证重构后的 GatewayService 和 NodeManager 能否正常协同工作
    """
    # 模拟 GatewayService 依赖
    with patch("app.services.openclaw.gateway.gateway.gateway_service.OpenClawTools"), \
         patch("app.services.openclaw.gateway.gateway.gateway_service.AsyncSessionLocal") as mock_session_cls:
        
        mock_session_cls.return_value.__aenter__.return_value = mock_db_session
        
        # 初始化服务
        gateway_service = OpenClawService()
        
        # 验证 GatewayService 是否能被实例化且属性存在
        assert gateway_service.dispatch_service is not None
        
        # 模拟 NodeManager 依赖
        # 注意：NodeManager 单例可能已被其他测试初始化，需要 reset 或者 patch
        NodeManager._instance = None
        
        with patch("app.services.openclaw.gateway.gateway.gateway_service.OpenClawService", return_value=gateway_service):
            # 确保 NodeManager 中的 openclaw_service 在 patch 后被正确设置
            # 因为 NodeManager 是单例，如果它之前已经被实例化，openclaw_service 可能是 None
            # 我们手动重置单例并重新获取
            NodeManager._instance = None
            
            # 我们需要 mock settings.OPENCLAW_BASE_URL 以确保 openclaw_service 被初始化
            with patch("app.core.config.settings.OPENCLAW_BASE_URL", "http://mock-url"):
                # 因为我们在 node_manager.service 中使用的是局部导入:
                # from app.services.openclaw.gateway.gateway.service import OpenClawService
                # 所以我们需要 patch 那个路径
                with patch("app.services.openclaw.gateway.gateway.gateway_service.OpenClawService", return_value=gateway_service):
                    node_manager = NodeManager.get_instance()
                    
                    # 验证 NodeManager 是否正确引用了 OpenClawService
                    assert node_manager.openclaw_service == gateway_service
                    
                    # 模拟指令分发
            # 我们不需要真的发网络请求，只需要验证调用链路通畅
            # 直接 mock running 和 client 对象
            with patch("app.services.openclaw.node.monitor.node_monitor_service.node_monitor.running", True):
                # 创建一个 Mock Client
                mock_client = AsyncMock()
                # is_connected 属性需要是一个 PropertyMock 或者直接设值
                # 这里我们直接设置属性
                mock_client.is_connected = True
                mock_client.request.return_value = {"status": "ok"}
                
                # 替换 node_monitor.client
                with patch.object(node_manager.openclaw_service.dispatch_service.http_client, "invoke") as mock_http_invoke:
                     # 实际上 node_manager dispatch_command 会调用 node_monitor (WS) 或者 HTTP
                     # 但我们这里测试的是 NodeManager -> Dispatch Command 逻辑
                     # 让我们看看 node_manager.dispatch_command 是如何实现的
                     # 它是通过 OpenClawService 还是直接 WS?
                     # 看了代码，NodeManager.dispatch_command 内部是:
                     # from app.services.openclaw.node.monitor.service import node_monitor
                     # if not node_monitor.running ...
                     # return await node_monitor.client.request(...)
                     
                     # 所以我们需要 mock node_monitor.client
                     with patch("app.services.openclaw.node.monitor.node_monitor_service.node_monitor.client", mock_client):
                        # Mock DB execute result for node query
                        # 我们需要模拟 db.execute(query).scalars().all()
                        # 注意：execute 返回的是一个 Result 对象， scalars() 返回一个 ScalarResult 对象， all() 返回列表
                        from unittest.mock import MagicMock
                        mock_result = MagicMock()
                        mock_scalars = MagicMock()
                        mock_scalars.all.return_value = [] # 模拟没有节点，或者根据需要模拟有节点
                        mock_result.scalars.return_value = mock_scalars
                        mock_db_session.execute.return_value = mock_result
                        
                        # 模拟有一个节点
                        mock_node = MagicMock()
                        mock_node.id = "node-1"
                        mock_node.status = "online"
                        mock_scalars.all.return_value = [mock_node]

                        # 调用分发逻辑
                        result = await node_manager.dispatch_command(
                            mock_db_session,
                            command="test",
                            params={},
                            target_nodes=["node-1"]
                        )
                        
                        # 验证结果
                        assert result["total"] == 1
                        assert result["sent"] == 1
                        mock_client.request.assert_called_once()
