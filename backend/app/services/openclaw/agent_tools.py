import json
import os
import asyncio
from typing import Any, Dict, Optional, List, Union
from datetime import datetime

from agno.tools import Toolkit
from agno.utils.log import log_debug, log_error, log_info
from app.core.config import settings
from app.services.openclaw.api_client import OpenClawHttpClient
from app.services.openclaw.ws_client import OpenClawWsClient  # 仅用于类型提示或特殊WS调用，主要逻辑已迁移

# 尝试导入fallback工具
try:
    from app.services.tools.bravesearch import BraveSearchTools
    BRAVE_AVAILABLE = True
except ImportError:
    BRAVE_AVAILABLE = False
    log_debug("BraveSearchTools not available, web_search fallback disabled")

try:
    from app.services.tools.trafilatura import TrafilaturaTools
    TRAFILATURA_AVAILABLE = True
except ImportError:
    TRAFILATURA_AVAILABLE = False
    log_debug("TrafilaturaTools not available, web_fetch fallback disabled")


class OpenClawTools(Toolkit):
    """
    OpenClaw 工具集 - 重构版
    
    核心变更：
    1. 默认使用 OpenClawHttpClient (RESTful) 处理控制面请求。
    2. 移除了混合的 WS 逻辑，确保工具调用的稳定性。
    3. WS 客户端 (OpenClawWsClient) 仅在 NodeMonitor 中单独实例化，不在工具层混用。
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
        enable_web_search: bool = True,
        enable_web_fetch: bool = True,
        enable_browser: bool = True,
        enable_cron: bool = True,
        enable_nodes: bool = True,
        enable_message: bool = True,
        enable_gateway: bool = True,
        enable_sessions: bool = True,
        enable_plugins: bool = True,
        all: bool = False,
        timeout: int = 20_000,
        fallback_enabled: bool = True,
        **kwargs,
    ):
        self.http_client = OpenClawHttpClient(
            base_url=base_url, 
            token=token, 
            timeout=timeout / 1000.0
        )
        self.fallback_enabled = fallback_enabled
        self.metrics = {}
        
        self.TOOLS_METADATA = {
            "web_search": {
                "description": "搜索网络信息，返回相关网页摘要",
                "params": {
                    "query": {"type": "str", "required": True, "desc": "搜索关键词"},
                    "count": {"type": "int", "required": False, "default": 5, "desc": "返回结果数量"},
                },
            },
            "web_fetch": {
                "description": "获取指定网页的详细内容",
                "params": {
                    "url": {"type": "str", "required": True, "desc": "网页URL"},
                    "extract_mode": {"type": "str", "required": False, "default": "markdown", "desc": "markdown/html/text"},
                },
            },
            "cron": {
                "description": "管理定时任务",
                "valid_actions": ["status", "list", "add", "remove", "run", "pause", "resume"],
                "params": {
                    "action": {"type": "str", "required": True, "desc": "status/list/add/remove/run/pause/resume"},
                    "job_id": {"type": "str", "required": False, "desc": "任务ID"},
                    "schedule": {"type": "str", "required": False, "desc": "cron表达式"},
                    "command": {"type": "str", "required": False, "desc": "命令"},
                },
            },
            "message": {
                "description": "发送即时消息到Slack/Discord/Telegram等",
                "valid_actions": ["send", "list_channels"],
                "params": {
                    "action": {"type": "str", "required": True, "desc": "send/list_channels"},
                    "channel": {"type": "str", "required": False, "desc": "目标频道"},
                    "content": {"type": "str", "required": False, "desc": "消息内容"},
                },
            },
            "nodes": {
                "description": "管理OpenClaw节点 (控制面操作)",
                "valid_actions": ["list", "status"],
                "params": {
                    "action": {"type": "str", "required": True, "desc": "list/status"},
                },
            },
            # 其他工具暂略，按需迁移
        }

        self._dynamic_funcs = {}
        for _name, meta in self.TOOLS_METADATA.items():
            func = self._create_tool_func(_name, meta)
            self._dynamic_funcs[_name] = func
            setattr(self, f"_dyn_{_name}", func)

        flag_map = {
            "web_search": enable_web_search,
            "web_fetch": enable_web_fetch,
            "cron": enable_cron,
            "message": enable_message,
            "nodes": enable_nodes,
        }
        tools = [self._dynamic_funcs[n] for n, enabled in flag_map.items() if all or enabled]
        
        super().__init__(name="openclaw_tools", tools=tools, **kwargs)

    async def aclose(self):
        await self.http_client.close()

    def _create_tool_func(self, tool_name: str, metadata: Dict[str, Any]):
        param_defs = metadata["params"]

        async def tool_func(**kwargs):
            # 1. 异步调用 HTTP 接口
            res = await self.http_client.invoke(tool_name, kwargs)
            
            # 2. 处理错误与 Fallback
            if "error" in res:
                if self.fallback_enabled:
                    fallback_res = self._fallback_invoke(tool_name, kwargs)
                    if "error" not in json.loads(fallback_res):
                        return fallback_res
                return json.dumps(res, ensure_ascii=False)
                
            return json.dumps(res, ensure_ascii=False)

        tool_func.__doc__ = metadata.get("description", "")
        tool_func.__name__ = f"oc_{tool_name}"
        return tool_func

    def _fallback_invoke(self, tool_name: str, params: Dict[str, Any]) -> str:
        if tool_name == "web_search" and BRAVE_AVAILABLE:
            try:
                bs = BraveSearchTools()
                result = bs.brave_search(query=params.get("query", ""), max_results=params.get("count", 5))
                return json.dumps({"source": "brave_fallback", "results": result}, ensure_ascii=False)
            except Exception: pass
            
        if tool_name == "web_fetch" and TRAFILATURA_AVAILABLE:
            try:
                tf = TrafilaturaTools()
                content = tf.extract_text(url=params.get("url"))
                return json.dumps({"source": "trafilatura_fallback", "content": content[:20000]}, ensure_ascii=False)
            except Exception: pass
            
        return json.dumps({"error": f"Tool {tool_name} unavailable (fallback failed)"}, ensure_ascii=False)

    # ── 兼容旧版异步方法 (供 Agent 直接调用) ──────────────────────────────────

    async def check_health_async(self) -> Dict[str, Any]:
        return await self.http_client.check_health()

    async def oc_web_search_async(self, query: str, count: int = 5) -> str:
        return await self._dynamic_funcs["web_search"](query=query, count=count)

    async def oc_web_fetch_async(self, url: str, extract_mode: str = "markdown") -> str:
        return await self._dynamic_funcs["web_fetch"](url=url, extract_mode=extract_mode)

    async def oc_cron_async(self, action: str, **kwargs) -> str:
        return await self._dynamic_funcs["cron"](action=action, **kwargs)

    async def oc_nodes_async(self, action: str, **kwargs) -> str:
        return await self._dynamic_funcs["nodes"](action=action, **kwargs)

    async def oc_plugins_async(self, action: str, **kwargs) -> str:
        # Assuming there is a 'plugins' tool or similar logic
        # If not defined in TOOLS_METADATA, we might need to add it or handle it here.
        # For now, let's assume it might be handled via generic invoke if not strictly a "tool"
        res = await self.http_client.invoke("plugins", {"action": action, **kwargs})
        return json.dumps(res, ensure_ascii=False)
