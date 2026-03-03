"""
应用场景：
    OpenClaw 网关交互的主入口点。
    用于 API 端点查询节点状态、活动、统计信息以及创建任务。

核心功能：
    - 网关健康检查与信息获取
    - 节点列表查询
    - 活动/作业列表查询
    - 统计数据聚合
    - 任务创建编排

__author__ = "xucao"
Created: 2024-05
Last Modified: 2025-03
"""

import json
import uuid
import traceback
from typing import List, Optional, Any, Dict
from fastapi import HTTPException
from datetime import datetime

from app.core.config import settings
from app.core.logger import logger
from app.schemas.openclaw import (
    OpenClawNode, OpenClawActivity, OpenClawStat, OpenClawPlugin,
    OpenClawHealth, OpenClawInfo
)
from app.services.openclaw.gateway.agent.tools import OpenClawTools
from app.services.openclaw.task.parser.task_parser_service import parse_task_intent
from app.services.openclaw.task.worker.task_worker_service import task_worker
from app.models.openclaw_task import OpenClawTask
from app.crud.crud_openclaw_task import OpenClawTaskCRUD
from app.db.session import AsyncSessionLocal

from app.services.openclaw.gateway.dispatch.dispatch_service import DispatchService

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
        
        # 初始化 DispatchService
        self.dispatch_service = DispatchService(self.tools.http_client)

    async def close(self):
        """Close resources"""
        if hasattr(self, "tools") and self.tools:
            await self.tools.aclose()

    async def invoke(self, tool: str, args: Dict[str, Any], session_key: Optional[str] = None) -> Dict[str, Any]:
        """Generic tool invocation via HTTP client"""
        return await self.tools.http_client.invoke(tool, args, session_key)

    async def chat_completion(self, messages: List[Dict[str, str]], model: str = "openclaw:main", stream: bool = True) -> Dict[str, Any]:
        """Chat completion via HTTP client"""
        logger.debug(f"Calling http_client.chat_completion: model={model}")
        try:
            return await self.tools.http_client.chat_completion(messages, model, stream)
        except Exception as e:
            logger.error(f"Service chat_completion failed: {e}")
            return {"error": str(e)}

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
            from app.services.openclaw.node.monitor.node_monitor_service import node_monitor
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
            from app.services.openclaw.node.monitor.node_monitor_service import node_monitor
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
                 except Exception as e:
                     logger.debug(f"Failed to parse nodes data: {e}")
                     pass

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
                    except Exception as e:
                        logger.debug(f"Failed to parse jobs data: {e}")
                        pass
            
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
                except Exception as e:
                    logger.debug(f"Failed to parse plugins data: {e}")
                    pass
                
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
        
        优化后的版本：
        1. 先持久化任务到数据库
        2. 异步分发到工作器
        3. 立即返回任务信息
        """
        try:
            # 1. Parse intent
            logger.info(f"Step 1/4: 正在解析任务意图: prompt='{prompt[:50]}'")
            task_data = await parse_task_intent(prompt, db)
            logger.info(f"任务意图解析成功: {json.dumps(task_data, ensure_ascii=False)}")
            
            # 意图过滤：如果是闲聊，直接返回
            if task_data.get("intent_type") == "chat":
                logger.info(f"用户意图为闲聊，跳过任务创建流程")
                
                # 尝试调用 OpenClaw 获取真实回复
                raw_command = task_data.get("command", "")
                # 移除可能的 "chat " 前缀 (不区分大小写)
                if raw_command.lower().startswith("chat "):
                    chat_content = raw_command[5:]
                else:
                    chat_content = raw_command
                
                chat_response_text = ""
                
                try:
                    logger.info(f"正在请求 OpenClaw 获取对话回复: {chat_content}")
                    # 使用 chat_completion 接口
                    chat_res = await self.chat_completion(
                        messages=[{"role": "user", "content": chat_content}],
                        model="openclaw:main",
                        stream=False
                    )
                    
                    if isinstance(chat_res, dict):
                         if "error" in chat_res:
                             logger.warning(f"OpenClaw 返回错误: {chat_res['error']}")
                             raise ValueError(f"OpenClaw Error: {chat_res['error']}")

                         # 处理非流式响应结构
                         # OpenAI format: choices[0].message.content
                         choices = chat_res.get("choices", [])
                         if choices and len(choices) > 0:
                             chat_response_text = choices[0].get("message", {}).get("content", "")
                         elif "content" in chat_res:
                             chat_response_text = chat_res["content"]
                             
                except Exception as e:
                    logger.warning(f"OpenClaw 对话请求失败，回退到兜底提示: {e}")
                    # Local fallback logic
                    chat_response_text = f"你好！我是 Tiga 智能体。虽然目前无法连接到 OpenClaw 大脑（{str(e)}），但我依然可以为您提供基础服务，例如本地知识库检索或简单的任务记录。请问有什么可以帮您？"
                
                # 如果最终没有获取到回复（为空），则使用默认提示
                if not chat_response_text:
                     chat_response_text = "虽然我明白了您的意图是闲聊，但我目前无法连接到大脑 (OpenClaw) 获取回复。您可以检查一下网络连接或网关状态。"
                
                return {
                    "task_id": None,
                    "status": "SKIPPED",
                    "message": "这是一个对话请求，不执行自动化任务",
                    "chat_response": chat_response_text
                }

            # 2. 持久化任务到数据库
            schedule_str = task_data.get("schedule", "0 9 * * *")
            command = task_data.get("command", "")
            
            # 解析 schedule 字符串为 datetime（如果是 cron 表达式，这里简化处理）
            schedule_dt = None
            if schedule_str and schedule_str != "0 9 * * *":  # 非默认时间
                pass
            
            logger.info(f"Step 2/4: 正在创建数据库任务记录: command='{command}'")
            task, created = await OpenClawTaskCRUD.create_task(
                db,
                original_prompt=prompt,
                parsed_command=task_data,
                schedule=schedule_dt,
                target_node_id=None  # 可以扩展支持指定节点
            )
            
            task_id = task.task_id
            logger.info(f"数据库任务记录创建完成: task_id={task_id}, created={created}")
            
            # 3. 异步分发任务到工作器
            if created and task.is_pending():
                logger.info(f"Step 3/4: 准备分发任务到工作器: task_id={task_id}")
                
                # 定义网关调用函数
                async def gateway_call():
                    # 使用独立的 Service 实例进行后台分发，避免请求上下文关闭导致的 Client closed 错误
                    # 临时导入以避免循环依赖
                    from app.services.openclaw.gateway.agent.tools import OpenClawTools
                    from app.services.openclaw.gateway.dispatch.dispatch_service import DispatchService
                    
                    logger.info(f"Worker: 初始化后台分发服务... task_id={task_id}")
                    
                    # 1. 初始化独立的工具集（包含新的 HTTP Client）
                    temp_tools = OpenClawTools(
                        base_url=self.base_url,
                        token=self.token,
                        fallback_enabled=True
                    )
                    
                    try:
                        # 2. 初始化分发服务
                        temp_dispatch_service = DispatchService(temp_tools.http_client)
                        
                        target_node = task.target_node_id or "gateway" 
                        
                        # 构建 payload
                        payload = {
                            "id": task.task_id,
                            "schedule": schedule_str,
                            "command": command,
                            "enabled": True
                        }
                        
                        logger.info(f"Worker: 调用 DispatchService 下发任务: task_id={task.task_id}, target={target_node}")
                        return await temp_dispatch_service.dispatch_to_gateway(
                            task_payload=payload,
                            node_id=target_node,
                            task_id=task.task_id
                        )
                    finally:
                        # 3. 确保资源释放
                        logger.info(f"Worker: 释放后台分发服务资源 task_id={task_id}")
                        await temp_tools.aclose()
                
                # 分发到工作器（不等待）
                await task_worker.dispatch_task(
                    task_id=task.task_id,
                    gateway_call_func=gateway_call,
                    db_session_factory=AsyncSessionLocal
                )
                logger.info(f"任务已成功加入工作队列: task_id={task_id}")
            else:
                logger.info(f"任务已存在或非待处理状态，跳过分发: task_id={task_id}, status={task.status}")
            
            # 4. 立即返回任务信息
            logger.info(f"Step 4/4: 返回任务创建结果: task_id={task_id}")
            return {
                "task_id": task.task_id,
                "status": task.status,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "is_new": created
            }
            
        except HTTPException as he:
            logger.error(f"任务创建流程HTTP异常: {he.detail}")
            raise
        except Exception as e:
            error_details = traceback.format_exc()
            logger.error(f"OpenClaw 任务创建流程严重错误: {str(e)}\n堆栈追踪:\n{error_details}")
            raise HTTPException(status_code=500, detail=f"任务流程执行失败: {str(e)}")