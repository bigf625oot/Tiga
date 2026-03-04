import json
import os
import asyncio
from typing import Any, Dict, Optional, List, Union
from datetime import datetime
from urllib.parse import urlparse

from agno.tools import Toolkit
from agno.utils.log import log_debug, log_error, log_info
from app.core.config import settings
from app.services.openclaw.clients.base_client import ConnectionError as WSConnectionError
from app.services.openclaw.clients.agno import AgnoGatewayClient

# 尝试导入fallback工具
try:
    from agno.tools.bravesearch import BraveSearchTools
    BRAVE_AVAILABLE = True
except ImportError:
    BRAVE_AVAILABLE = False
    log_debug("BraveSearchTools not available, web_search fallback disabled")

try:
    from agno.tools.trafilatura import TrafilaturaTools
    TRAFILATURA_AVAILABLE = True
except ImportError:
    TRAFILATURA_AVAILABLE = False
    log_debug("TrafilaturaTools not available, web_fetch fallback disabled")


class OpenClawTools(Toolkit):
    """
    OpenClaw 工具集 - WebSocket 重构版
    
    核心变更：
    1. 强制使用 AgnoGatewayClient (WebSocket) 处理控制面请求，完全禁用 HTTP。
    2. 实现了 Agno 智能体控制面的纯 WS 通信要求。
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
        timeout: int = 60_000, # Increased for WS blocking wait
        fallback_enabled: bool = True,
        **kwargs,
    ):
        super().__init__(name="openclaw_tools", **kwargs)

        # WebSocket Client Initialization
        ws_url = settings.OPENCLAW_WS_URL or base_url or "ws://localhost:8000"
        parsed_ws = urlparse(ws_url)
        if parsed_ws.scheme not in ("ws", "wss"):
            raise ValueError("OpenClawTools 仅支持 ws/wss 协议，请配置 OPENCLAW_WS_URL 或传入 ws/wss base_url")
            
        api_key = token or getattr(settings, "OPENCLAW_AGNO_KEY", None) or "test-key"
        api_secret = getattr(settings, "OPENCLAW_AGNO_SECRET", None) or "test-secret"
        
        self.client = AgnoGatewayClient(
            gateway_url=ws_url,
            api_key=api_key,
            api_secret=api_secret
        )
        
        self.fallback_enabled = fallback_enabled
        self.timeout = timeout
        
        # Register Tools
        if all or enable_web_search:
            self.register(self.web_search)
        if all or enable_web_fetch:
            self.register(self.web_fetch)
        if all or enable_cron:
            self.register(self.cron_manage)
        if all or enable_message:
            self.register(self.send_message)
        if all or enable_nodes:
            self.register(self.manage_nodes)

    async def _execute_ws(self, task_type: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """通过 WebSocket 执行任务"""
        if not self.client.is_connected:
            await self.client.connect()
            
        try:
            # 使用 execute_task 阻塞等待结果
            # 注意：gateway 端的 execute 期望参数是 payload
            result_event = await self.client.execute_task(
                task_type=task_type,
                target=args.get("url") or args.get("target") or "unknown",
                payload=args,
                timeout=self.timeout / 1000.0
            )
            
            method = result_event.get("method")
            params = result_event.get("params", {})
            
            if method == "task_completed":
                return {"ok": True, "result": params.get("result")}
            elif method == "task_failed":
                return {"ok": False, "error": params.get("error")}
            else:
                return {"ok": False, "status": method}
                
        except TimeoutError:
            return {"ok": False, "error": "Task execution timed out"}
        except Exception as e:
            if isinstance(e, WSConnectionError):
                log_error(
                    f"WS Execution Error: disconnected context={self.client.last_disconnect_context} detail={e}"
                )
            else:
                log_error(f"WS Execution Error: {e}")
            return {"ok": False, "error": str(e)}

    async def web_search(self, query: str, count: int = 5) -> str:
        """
        Search the web for a query.
        
        Args:
            query (str): The search query.
            count (int): Number of results to return.
        """
        log_info(f"OpenClaw: Searching web for '{query}'")
        res = await self._execute_ws("web_search", {"query": query, "count": count})
        
        if res.get("ok"):
            return json.dumps(res["result"], ensure_ascii=False)
            
        if self.fallback_enabled and BRAVE_AVAILABLE:
            log_info("OpenClaw: Falling back to local search")
            try:
                bs = BraveSearchTools()
                result = bs.brave_search(query=query, max_results=count)
                return json.dumps(result, ensure_ascii=False)
            except Exception as e:
                return f"Error: {res.get('error')} (Fallback failed: {e})"
            
        return f"Error: {res.get('error')}"

    async def web_fetch(self, url: str, extract_mode: str = "markdown") -> str:
        """
        Fetch and extract content from a URL.
        
        Args:
            url (str): The URL to fetch.
            extract_mode (str): Extraction mode (markdown, text, html).
        """
        log_info(f"OpenClaw: Fetching {url}")
        res = await self._execute_ws("web_fetch", {"url": url, "extractMode": extract_mode})
        
        if res.get("ok"):
             return json.dumps(res["result"], ensure_ascii=False)
             
        if self.fallback_enabled and TRAFILATURA_AVAILABLE:
            try:
                tf = TrafilaturaTools()
                content = tf.extract_text(url=url)
                return json.dumps({"content": content[:20000]}, ensure_ascii=False)
            except Exception as e:
                 return f"Error: {res.get('error')} (Fallback failed: {e})"
            
        return f"Error: {res.get('error')}"

    async def cron_manage(self, action: str, job_id: str = None, schedule: str = None, command: str = None) -> str:
        """
        Manage cron jobs.
        
        Args:
            action (str): status/list/add/remove/run/pause/resume
            job_id (str): Job ID (optional)
            schedule (str): Cron schedule (optional)
            command (str): Command to run (optional)
        """
        res = await self._execute_ws("cron", {
            "action": action, 
            "job_id": job_id, 
            "schedule": schedule, 
            "command": command
        })
        return json.dumps(res, ensure_ascii=False)

    async def send_message(self, action: str, channel: str = None, content: str = None) -> str:
        """
        Send instant messages.
        
        Args:
            action (str): send/list_channels
            channel (str): Target channel
            content (str): Message content
        """
        res = await self._execute_ws("message", {
            "action": action,
            "channel": channel,
            "content": content
        })
        return json.dumps(res, ensure_ascii=False)

    async def manage_nodes(self, action: str) -> str:
        """
        Manage OpenClaw nodes.
        
        Args:
            action (str): list/status
        """
        res = await self._execute_ws("nodes", {"action": action})
        return json.dumps(res, ensure_ascii=False)

    async def aclose(self, reason: str = "tools_aclose"):
        await self.client.close(reason=reason)
