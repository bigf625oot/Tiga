"""
基于智能体 (Agent)，实现以下商业场景：
1.分布式云手机/云控系统：控制成百上千台设备自动执行社交媒体任务。
2.大规模探测/爬虫引擎：利用不同节点的 IP 资源规避反爬。
3.边缘计算执行器：在各地的边缘节点部署任务，实时处理本地数据。

author: xucao
date: 2026-03-03
"""

from .gateway.gateway.gateway_service import OpenClawService
from .gateway.agent.tools import OpenClawTools
from .node.manager.node_manager_service import NodeManager, node_manager
from .node.monitor.node_monitor_service import NodeMonitor, node_monitor
from .node.auth.node_auth_service import DeviceIdentityManager

__all__ = [
    "OpenClawService",
    "OpenClawTools",
    "NodeManager",
    "node_manager",
    "NodeMonitor",
    "node_monitor",
    "DeviceIdentityManager",
    "__version_info__",
    "__author__",
    "__description__",
    "__success_response__",
]

