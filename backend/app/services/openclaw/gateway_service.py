import json
import uuid
from typing import List, Optional, Any, Dict
from fastapi import HTTPException

from app.core.config import settings
from app.core.logger import logger
from app.schemas.openclaw import (
    OpenClawNode, OpenClawActivity, OpenClawStat, OpenClawPlugin,
    OpenClawHealth, OpenClawInfo
)
from app.services.openclaw.agent_tools import OpenClawTools
from app.services.openclaw.task_parser import parse_task_intent

class OpenClawService:
    def __init__(self):
        self.base_url = settings.OPENCLAW_BASE_URL
        self.token = settings.OPENCLAW_GATEWAY_TOKEN or settings.OPENCLAW_TOKEN
        
        if not self.base_url:
            logger.error("OPENCLAW_BASE_URL not set in settings/env. OpenClaw integration will fail.")
            # We don't raise here to allow service instantiation, but methods will fail or check
            
        self.tools = OpenClawTools(
            base_url=self.base_url,
            token=self.token,
            fallback_enabled=True,
            enable_plugins=True
        )

    async def close(self):
        """Close resources"""
        if hasattr(self, "tools") and self.tools:
            await self.tools.aclose()

    async def invoke(self, tool: str, args: Dict[str, Any], session_key: Optional[str] = None) -> Dict[str, Any]:
        """Generic tool invocation via HTTP client"""
        return await self.tools.http_client.invoke(tool, args, session_key)

    async def chat_completion(self, messages: List[Dict[str, str]], model: str = "openclaw:main", stream: bool = True) -> Dict[str, Any]:
        """Chat completion via HTTP client"""
        return await self.tools.http_client.chat_completion(messages, model, stream)

    async def check_health(self) -> OpenClawHealth:
        """Check OpenClaw Gateway health"""
        # 1. Try HTTP check via tools
        try:
            health_data = await self.tools.check_health_async()
        except Exception:
            health_data = {"available": False}
        
        # 2. Check WS status via NodeMonitor
        # If WS is connected, we consider the service available even if HTTP fails
        try:
            from app.services.openclaw.node_monitor import node_monitor
            if node_monitor.running and node_monitor.client.is_connected:
                health_data["available"] = True
                if health_data.get("version") == "unknown" or not health_data.get("version"):
                    health_data["version"] = "connected (ws)"
        except ImportError:
            pass

        return OpenClawHealth(
            available=health_data.get("available", False),
            version=health_data.get("version"),
            base_url=self.base_url or "",
            tools_enabled=list(self.tools.TOOLS_METADATA.keys()),
            metrics=self.tools.metrics,
            fallback_enabled=self.tools.fallback_enabled
        )

    async def get_info(self) -> OpenClawInfo:
        """Get OpenClaw Gateway connection info"""
        
        # 1. Try to get info via WebSocket (Preferred)
        ws_info = {}
        ws_connected = False
        try:
            from app.services.openclaw.node_monitor import node_monitor
            if node_monitor.running and node_monitor.client.is_connected:
                # Use "config.get" to fetch current configuration
                ws_res = await node_monitor.client.request("config.get", {}, timeout=5.0)
                if isinstance(ws_res, dict):
                    ws_info = ws_res
                    ws_connected = True
        except Exception as e:
            logger.warning(f"Failed to get info via WS: {e}")

        # 2. Try to get info from remote Gateway API (Fallback)
        remote_info = {}
        if not ws_connected:
            remote_info = await self.tools.http_client.get_gateway_info()
        
        # Merge info, preferring WS over HTTP
        info_source = ws_info if ws_connected else remote_info
        is_remote_ok = ws_connected or ("error" not in remote_info)
        
        # Base URL
        gateway_url = info_source.get("gateway_url") or info_source.get("baseUrl")
        if not gateway_url and is_remote_ok:
             gateway_url = self.base_url
        if not gateway_url:
            gateway_url = self.base_url

        # WebSocket URL
        ws_url = info_source.get("websocket_url") or info_source.get("wsUrl")
        if not ws_url and gateway_url:
             # Fallback derivation
            if gateway_url.startswith("https://"):
                ws_url = "wss://" + gateway_url[8:]
            elif gateway_url.startswith("http://"):
                ws_url = "ws://" + gateway_url[7:]
            elif gateway_url.startswith("ws"):
                 ws_url = gateway_url

        version = info_source.get("version", "unknown")
        
        # Determine status
        if is_remote_ok:
            status = "active"
        else:
            # Fallback check
            health = await self.check_health()
            status = "active" if health.available else "offline"
            if health.version:
                version = health.version

        return OpenClawInfo(
            gateway_url=gateway_url,
            websocket_url=ws_url,
            gateway_token=self.token,
            session_secret=settings.SECRET_KEY,
            status=status,
            version=version
        )

    async def list_nodes(self) -> List[OpenClawNode]:
        """List all connected nodes"""
        try:
            res_str = await self.tools.oc_nodes_async(action="list")
            
            try:
                res = json.loads(res_str)
            except json.JSONDecodeError:
                return []

            if isinstance(res, dict) and "error" in res:
                # Suppress connection errors
                if "connection" not in str(res['error']).lower():
                    logger.warning(f"OpenClaw nodes error: {res['error']}")
                return []
                
            nodes_data = []
            if isinstance(res, list):
                nodes_data = res
            elif isinstance(res, dict):
                # Try various response formats
                nodes_data = res.get("result") or res.get("nodes") or []
                if isinstance(nodes_data, str):
                     try:
                         parsed = json.loads(nodes_data)
                         nodes_data = parsed if isinstance(parsed, list) else parsed.get("nodes", [])
                     except: pass

            if not isinstance(nodes_data, list):
                nodes_data = []

            nodes = []
            for n in nodes_data:
                nodes.append(OpenClawNode(
                    id=str(n.get("id", "unknown")),
                    name=n.get("name", "Unknown Node"),
                    platform=n.get("platform", "unknown"),
                    status=n.get("status", "unknown"),
                    version=n.get("version"),
                    address=n.get("address")
                ))
            return nodes
        except Exception as e:
            logger.error(f"Failed to fetch nodes: {e}")
            return []

    async def list_activities(self) -> List[OpenClawActivity]:
        """List all scheduled activities/tasks"""
        try:
            res_str = await self.tools.oc_cron_async(action="list")
            
            try:
                res = json.loads(res_str)
            except json.JSONDecodeError:
                logger.warning(f"OpenClaw activities invalid JSON: {res_str}")
                return []
            
            if isinstance(res, dict) and "error" in res:
                # Suppress connection errors to avoid log spam, as health check handles availability
                if "connection" not in str(res['error']).lower():
                    logger.warning(f"OpenClaw activities error: {res['error']}")
                return []

            jobs_data = []
            if isinstance(res, dict):
                jobs_data = res.get("jobs") or res.get("result") or []
                if isinstance(jobs_data, dict): # result might be a dict with jobs
                    jobs_data = jobs_data.get("jobs", [])
                elif isinstance(jobs_data, str):
                    try:
                        parsed = json.loads(jobs_data)
                        jobs_data = parsed.get("jobs", [])
                    except: pass
            
            if not isinstance(jobs_data, list):
                jobs_data = []
            
            activities = []
            for job in jobs_data:
                cmd = (job.get("command") or "").lower()
                atype = "cron"
                if "crawl" in cmd: atype = "crawl"
                elif "screenshot" in cmd: atype = "screenshot"
                elif "monitor" in cmd: atype = "monitor"
                
                activities.append(OpenClawActivity(
                    id=str(job.get("id", "")),
                    name=job.get("name", job.get("id")),
                    type=atype,
                    status="active" if job.get("enabled", True) else "paused",
                    schedule=job.get("schedule"),
                    last_run=job.get("lastRun"),
                    next_run=job.get("nextRun"),
                    description=job.get("command")
                ))
            return activities
        except Exception as e:
            logger.error(f"Failed to fetch activities: {e}")
            return []

    async def list_plugins(self) -> List[OpenClawPlugin]:
        """List installed plugins"""
        try:
            res_str = await self.tools.oc_plugins_async(action="list")
            res = json.loads(res_str)
            
            if isinstance(res, dict) and "error" in res:
                logger.warning(f"OpenClaw plugins error: {res['error']}")
                return []
                
            plugins_data = res.get("plugins") or res.get("result") or []
            if isinstance(plugins_data, str):
                try:
                    plugins_data = json.loads(plugins_data)
                except: pass
                
            if not isinstance(plugins_data, list):
                 plugins_data = []
                 
            plugins = []
            for p in plugins_data:
                plugins.append(OpenClawPlugin(
                    name=p.get("name", "Unknown"),
                    version=p.get("version"),
                    status=p.get("status", "unknown"),
                    description=p.get("description")
                ))
            return plugins
        except Exception as e:
            logger.error(f"Failed to fetch plugins: {e}")
            return []

    async def get_stats(self) -> List[OpenClawStat]:
        """Get aggregated stats"""
        # Reuse list_activities logic
        activities = await self.list_activities()
        counts = {"crawl": 0, "monitor": 0, "screenshot": 0, "cron": 0}
        
        for act in activities:
            if act.type in counts:
                counts[act.type] += 1
            else:
                counts["cron"] += 1
        
        return [
            OpenClawStat(
                label="抓取", 
                count=counts["crawl"], 
                trend="+0%", 
                trendUp=True, 
                accentColor="from-blue-500 to-indigo-600"
            ),
            OpenClawStat(
                label="监控", 
                count=counts["monitor"], 
                trend="+0%", 
                trendUp=True, 
                accentColor="from-purple-500 to-pink-600"
            ),
            OpenClawStat(
                label="截图", 
                count=counts["screenshot"], 
                trend="+0%", 
                trendUp=True, 
                accentColor="from-emerald-500 to-teal-600"
            ),
            OpenClawStat(
                label="定时", 
                count=counts["cron"], 
                trend="+0%", 
                trendUp=True, 
                accentColor="from-orange-500 to-red-600"
            ),
        ]

    async def create_task(self, prompt: str, db: Any) -> Dict[str, Any]:
        """
        Create a new automation task based on natural language prompt.
        """
        try:
            # 1. Parse intent
            task_data = await parse_task_intent(prompt, db)
            
            # 2. Generate ID
            job_id = f"task_{uuid.uuid4().hex[:8]}"
            
            # 3. Call the tool
            try:
                # 尝试通过 WebSocket 调用 (优先)
                # 使用局部导入避免循环依赖
                from app.services.openclaw.node_monitor import node_monitor
                
                # 初始化结果变量
                res = None
                
                if node_monitor.running and node_monitor.client.is_connected:
                    try:
                        # 构造参数（根据 WS 协议调整）
                        ws_res = await node_monitor.client.request("cron.add", {
                            "id": job_id,
                            "schedule": task_data.get("schedule", "0 9 * * *"),
                            "command": task_data.get("command", ""),
                            "enabled": True
                        }, timeout=10.0)
                        
                        if isinstance(ws_res, dict):
                            res = ws_res
                        else:
                            # 即使 WS 调用返回格式不对，也记录日志并让其回退
                            logger.warning(f"Invalid WS response for cron.add: {ws_res}")
                    except Exception as ws_e:
                        logger.warning(f"Task creation via WS failed: {ws_e}")
                
                # 如果 WS 未连接或调用失败，回退到 HTTP 调用
                if res is None:
                    # 使用 invoke 而不是直接调用工具方法，以获取更好的错误处理
                    res = await self.tools.http_client.invoke("cron", {
                        "action": "add",
                        "id": job_id,
                        "schedule": task_data.get("schedule", "0 9 * * *"),
                        "command": task_data.get("command", ""),
                        "enabled": True
                    })

            except Exception as e:
                # 全局异常捕获，确保不崩溃
                logger.error(f"Task creation unexpected error: {e}")
                # 不要直接抛出 500，而是构造一个包含错误信息的响应，让下面的逻辑处理
                res = {"error": f"Unexpected error: {str(e)}"}
            
            if isinstance(res, dict) and "error" in res:
                 error_msg = res['error']
                 # 如果是连接失败，给出更具体的提示
                 if "Connection failed" in str(error_msg) or "All connection attempts failed" in str(error_msg):
                     error_msg = "无法连接 OpenClaw 网关。请检查 .env 配置或确保网关已启动。"
                 
                 logger.error(f"OpenClaw tool error: {error_msg}")
                 raise HTTPException(status_code=503, detail=error_msg)
                 
            task_data["id"] = job_id
            return {"status": "success", "task": task_data}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"OpenClaw execution failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
