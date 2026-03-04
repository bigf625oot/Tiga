"""
基于智能体 (Agent)，实现以下商业场景：
1.分布式云手机/云控系统：控制成百上千台设备自动执行社交媒体任务。
2.大规模探测/爬虫引擎：利用不同节点的 IP 资源规避反爬。
3.边缘计算执行器：在各地的边缘节点部署任务，实时处理本地数据。

author: xucao
date: 2026-03-03
"""
from importlib import import_module
from typing import Any

_EXPORTS = {
    "OpenClawService": ("app.services.openclaw.gateway.service", "OpenClawService"),
    "OpenClawTools": ("app.services.openclaw.gateway.tools", "OpenClawTools"),
    "NodeManager": ("app.services.openclaw.node.manager", "NodeManager"),
    "node_manager": ("app.services.openclaw.node.manager", "node_manager"),
    "NodeMonitor": ("app.services.openclaw.node.monitor", "NodeMonitor"),
    "node_monitor": ("app.services.openclaw.node.monitor", "node_monitor"),
    "DeviceIdentityManager": ("app.services.openclaw.node.auth", "DeviceIdentityManager"),
}

__all__ = list(_EXPORTS.keys())


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(name)
    module_path, attr_name = _EXPORTS[name]
    module = import_module(module_path)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value
