import logging

import uuid
from typing import List, Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

import traceback
from app.core.logger import logger
from app.core.structured_logger import get_structured_logger
from app.api.deps import get_db, get_current_user_id, get_current_user_id_optional
from app.schemas.openclaw import (
    OpenClawNode, OpenClawActivity, OpenClawStat, OpenClawPlugin,
    CreateTaskRequest, OpenClawHealth, OpenClawInfo, ToolsInvokeRequest
)
from app.services.openclaw.gateway.service import OpenClawService

s_logger = get_structured_logger("openclaw.api")

router = APIRouter()
 
async def get_service():
    logger.debug("正在初始化 OpenClawService 实例...")
    service = OpenClawService()
    try:
        yield service
    finally:
        logger.debug("正在关闭 OpenClawService 实例连接... reason=request_scope_cleanup")
        await service.close(reason="request_scope_cleanup")
 
@router.get("/health", response_model=OpenClawHealth)
async def check_health(service: OpenClawService = Depends(get_service)):
    """检查 OpenClaw 网关健康状态
    
    端点: /health
    参考: [health.ts](src/gateway/server-methods/health.ts#L10-L38)
    """
    logger.info("收到健康检查请求...")
    try:
        health_status = await service.check_health()
        if health_status.available:
            logger.info(f"OpenClaw 状态正常")
        else:
            logger.warning(f"OpenClaw 响应异常: available={health_status.available}, version={health_status.version}")
        return health_status
    except Exception as e:
        logger.error(f"健康检查执行失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="无法连接到 OpenClaw 网关")

@router.get("/info", response_model=OpenClawInfo)
async def get_info(service: OpenClawService = Depends(get_service)):
    """获取 OpenClaw 网关连接配置信息"""
    logger.info("正在获取 OpenClaw 网关元数据信息...")
    try:
        info = await service.get_info()
        logger.debug(f"成功获取网关信息: {info}")
        return info
    except Exception as e:
        logger.error(f"获取网关信息失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取网关信息失败")
 

# ⚠️ 修正：/nodes 需要通过WebSocket调用 node.list 方法
# 参考实现：[nodes.ts](src/gateway/server-methods/nodes.ts#L415-L480)
from app.models.openclaw_task import OpenClawTask
from app.models.node import Node
from sqlalchemy import select, desc, func
from datetime import datetime, timedelta

# ... (imports)

@router.get("/activities", response_model=List[OpenClawActivity])
async def list_activities(
    limit: int = 50,
    service: OpenClawService = Depends(get_service),
    db: AsyncSession = Depends(get_db)
):
    """
    获取最近的活动记录
    优先从数据库查询 openclaw_tasks 表
    """
    try:
        stmt = select(OpenClawTask).order_by(desc(OpenClawTask.created_at)).limit(limit)
        result = await db.execute(stmt)
        tasks = result.scalars().all()
        
        activities = []
        for task in tasks:
            # 推断类型
            atype = "cron"
            cmd_str = str(task.parsed_command).lower()
            if "crawl" in cmd_str: atype = "crawl"
            elif "screenshot" in cmd_str: atype = "screenshot"
            elif "monitor" in cmd_str: atype = "monitor"
            
            activities.append(OpenClawActivity(
                id=task.task_id,
                name=f"Task-{task.task_id[:8]}",
                type=atype,
                status=task.status,
                schedule=task.schedule.isoformat() if task.schedule else None,
                last_run=task.updated_at.isoformat() if task.updated_at else task.created_at.isoformat(),
                description=task.original_prompt[:100]
            ))
        return activities
    except Exception as e:
        logger.error(f"Failed to fetch activities from DB: {e}")
        return []

@router.get("/stats", response_model=List[OpenClawStat])
async def get_stats(
    service: OpenClawService = Depends(get_service),
    db: AsyncSession = Depends(get_db)
):
    """
    获取系统统计数据
    从数据库聚合 openclaw_tasks 统计信息
    """
    try:
        # 统计各类型任务数量 (简化版：根据 status 统计)
        # SELECT status, count(*) FROM openclaw_tasks GROUP BY status
        stmt = select(OpenClawTask.status, func.count(OpenClawTask.task_id)).group_by(OpenClawTask.status)
        result = await db.execute(stmt)
        stats_map = {row[0]: row[1] for row in result.all()}
        
        # 构造返回数据
        # 暂时将 status 映射为前端展示的 label
        # 实际业务中可能需要根据 parsed_command 解析具体类型 (crawl/monitor/screenshot)
        
        # 再次查询具体类型的数量 (需要解析 JSON，这里简化处理，只查总数和状态)
        total_tasks = sum(stats_map.values())
        failed_tasks = stats_map.get("FAILED", 0)
        pending_tasks = stats_map.get("PENDING", 0)
        dispatched_tasks = stats_map.get("DISPATCHED", 0)
        
        return [
            OpenClawStat(
                label="总任务", 
                count=total_tasks, 
                trend="+0%", 
                trendUp=True, 
                accentColor="from-blue-500 to-indigo-600"
            ),
            OpenClawStat(
                label="待处理", 
                count=pending_tasks, 
                trend="+0%", 
                trendUp=True, 
                accentColor="from-orange-500 to-yellow-600"
            ),
            OpenClawStat(
                label="执行中", 
                count=dispatched_tasks, 
                trend="+0%", 
                trendUp=True, 
                accentColor="from-emerald-500 to-teal-600"
            ),
            OpenClawStat(
                label="已失败", 
                count=failed_tasks, 
                trend="+0%", 
                trendUp=False, 
                accentColor="from-red-500 to-pink-600"
            ),
        ]
    except Exception as e:
        logger.error(f"Failed to fetch stats from DB: {e}")
        return []

@router.get("/nodes", response_model=List[OpenClawNode])
async def list_nodes(
    service: OpenClawService = Depends(get_service),
    db: AsyncSession = Depends(get_db)
):
    """
    列出所有已连接的节点
    优先尝试 WebSocket 获取，失败则回退查询数据库
    """
    logger.info("正在请求 OpenClaw 节点列表...")
    
    # 方案1: 通过WebSocket客户端调用（推荐）
    nodes = await service.list_nodes()
    
    if not nodes:
        # 方案2: 回退查询数据库
        logger.info("WebSocket 获取节点为空，尝试从数据库查询...")
        try:
            stmt = select(Node)
            result = await db.execute(stmt)
            db_nodes = result.scalars().all()
            
            nodes = []
            for n in db_nodes:
                nodes.append(OpenClawNode(
                    id=n.id,
                    name=n.name or "Unknown",
                    platform=n.platform or "unknown",
                    status=n.status.value if hasattr(n.status, 'value') else str(n.status),
                    version=n.version,
                    address=n.ip_address
                ))
        except Exception as e:
            logger.error(f"Failed to fetch nodes from DB: {e}")
    
    logger.info(f"节点获取成功，当前节点数: {len(nodes)}")
    return nodes
 
# ⚠️ 修正：OpenClaw Gateway 不提供 activities 端点
# 建议通过 session 查询或日志订阅实现
@router.get("/activities", response_model=List[OpenClawActivity])
async def list_activities(
    limit: int = 50,
    service: OpenClawService = Depends(get_service)
):
    """
    获取最近的活动记录
    
    注意：OpenClaw Gateway 不提供直接的 activities API
    建议通过以下方式实现：
    1. 订阅 WebSocket 事件获取实时活动
    2. 查询 session history
    3. 解析日志文件
    """
    logger.warning("activities 端点需要自定义实现，暂返回空列表")
    
    # 临时实现：返回空列表
    # 实际项目中应该：
    # 1. 建立 WebSocket 连接订阅事件
    # 2. 持久化事件到数据库
    # 3. 从数据库查询
    return []
 
# ⚠️ 修正：OpenClaw Gateway 不提供 RESTful plugins API
# 插件信息通过 CLI 获取: openclaw plugins list
@router.get("/plugins", response_model=List[OpenClawPlugin])
async def list_plugins(service: OpenClawService = Depends(get_service)):
    """
    列出已加载的插件
    
    注意：OpenClaw Gateway 不提供 HTTP 端点获取插件列表
    需要通过 CLI 调用或 WebSocket 订阅
    
    参考: [Plugin SDK](26-plugin-sdk-and-development)
    """
    logger.warning("plugins 端点需要通过 CLI 或 WebSocket 获取")
    
    # 临时实现：调用 CLI 或使用缓存
    # plugins = await service.run_cli_command(["openclaw", "plugins", "list"])
    
    return []
 
# stats 信息通过 WebSocket health 方法获取
@router.get("/stats", response_model=List[OpenClawStat])
async def get_stats(service: OpenClawService = Depends(get_service)):
    """
    获取系统统计数据
    
    注意：OpenClaw Gateway 通过 WebSocket health 方法返回统计信息
    参考: [health.ts](src/gateway/server-methods/health.ts#L10-L38)
    """
    logger.info("正在提取 OpenClaw 性能统计数据...")
    
    # 通过WebSocket调用 health 方法
    # stats = await service.call_ws_method("health", {"probe": True})
    
    # 临时实现：返回空列表
    return []
 
# 使用 /tools/invoke 创建任务
@router.post("/create_task")
async def create_task(
    request: CreateTaskRequest, 
    db: AsyncSession = Depends(get_db),
    service: OpenClawService = Depends(get_service),
    user_id: Optional[str] = Depends(get_current_user_id_optional)
):
    """
    根据自然语言提示创建新的自动化任务
    """
    trace_id = uuid.uuid4().hex
    user_id = user_id or "anonymous"
    
    with s_logger.context(
        "create_task", 
        trace_id=trace_id, 
        user_id=user_id,
        prompt_preview=request.prompt[:50]
    ):
        try:
            # 增加详细的中文日志记录
            logger.info(f"开始创建任务: trace_id={trace_id}, user={user_id}, prompt='{request.prompt[:100]}'")
            
            # 使用 Service 层的 create_task 方法，它包含了意图解析和工具调用逻辑
            result = await service.create_task(request.prompt, db)
            
            # 尝试从 result 中获取 task_id
            task_id = result.get("task", {}).get("id") or result.get("task_id")
            if task_id:
                s_logger.info("任务创建成功", task_id=task_id, trace_id=trace_id)
            else:
                s_logger.warning("任务创建返回结果缺少 task_id", result=result, trace_id=trace_id)
            
            return result
            
        except ValueError as ve:
            # s_logger.context will catch exception but we need to map to 400
            error_msg = f"任务创建参数验证失败: {str(ve)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            raise HTTPException(status_code=400, detail=str(ve))
        except HTTPException as he:
            logger.error(f"任务创建HTTP异常: {he.detail}\n{traceback.format_exc()}")
            raise
        except Exception as e:
            error_msg = f"任务创建未知失败: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            raise HTTPException(status_code=500, detail="任务创建失败，请联系管理员")
 
# 通过工具调用方式访问 Gateway 功能
@router.post("/tools/invoke")
async def tools_invoke(
    request: ToolsInvokeRequest,
    service: OpenClawService = Depends(get_service)
):
    """
    统一工具调用接口
    
    端点对应: /tools/invoke
    参考: [tools-invoke-http.ts](src/gateway/tools-invoke-http.ts#L134-L200)
    """
    # 兼容 session_key 和 sessionKey
    session_key = request.session_key or request.sessionKey
    
    result = await service.invoke(request.tool, request.args, session_key)
    return result
 
# OpenAI 兼容的对话接口
@router.post("/chat/completions")
async def chat_completions(
    model: str = "openclaw:main",
    messages: List[Dict[str, str]] = [],
    stream: bool = True,
    service: OpenClawService = Depends(get_service)
):
    """
    OpenAI 兼容的对话接口
    
    端点对应: /v1/chat/completions
    参考: [openai-http.ts](src/gateway/openai-http.ts#L202-L220)
    """
    try:
        logger.info(f"收到对话请求: model={model}, stream={stream}, messages_count={len(messages)}")
        if messages:
            last_msg = messages[-1].get("content", "")[:50]
            logger.info(f"最后一条消息: {last_msg}")
        
        result = await service.chat_completion(
            messages=messages,
            model=model,
            stream=stream
        )
        
        # 简单记录结果状态
        if isinstance(result, dict) and "error" in result:
             logger.error(f"对话请求返回错误: {result['error']}")
        else:
             logger.info("对话请求处理完成")
             
        return result
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"对话接口发生严重错误: {str(e)}\n{error_details}")
        raise HTTPException(status_code=500, detail=f"对话请求失败: {str(e)}")
