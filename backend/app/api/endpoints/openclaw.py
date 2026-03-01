import logging
from typing import List, Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
 
from app.core.logger import logger  
from app.api.deps import get_db
from app.schemas.openclaw import (
    OpenClawNode, OpenClawActivity, OpenClawStat, OpenClawPlugin,
    CreateTaskRequest, OpenClawHealth, OpenClawInfo
)
from app.services.openclaw import OpenClawService

router = APIRouter()
 
async def get_service():
    logger.debug("正在初始化 OpenClawService 实例...")
    service = OpenClawService()
    try:
        yield service
    finally:
        logger.debug("正在关闭 OpenClawService 实例连接...")
        await service.close()
 
@router.get("/health", response_model=OpenClawHealth)
async def check_health(service: OpenClawService = Depends(get_service)):
    """检查 OpenClaw 网关健康状态
    
    端点: /health
    参考: [health.ts](src/gateway/server-methods/health.ts#L10-L38)
    """
    logger.info("收到健康检查请求...")
    try:
        health_status = await service.check_health()
        if health_status.get("available"):
            logger.info(f"OpenClaw 状态正常")
        else:
            logger.warning(f"OpenClaw 响应异常: {health_status.get('error')}")
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
@router.get("/nodes", response_model=List[OpenClawNode])
async def list_nodes(service: OpenClawService = Depends(get_service)):
    """
    列出所有已连接的节点
    
    注意：OpenClaw Gateway 不提供 RESTful API 获取节点列表
    需要通过WebSocket调用 node.list 方法
    """
    logger.info("正在请求 OpenClaw 节点列表...")
    
    # 方案1: 通过WebSocket客户端调用（推荐）
    nodes = await service.list_nodes_via_ws()
    
    # 方案2: 临时替代 - 通过工具调用获取节点信息
    # nodes = await service.invoke("nodes", {"action": "list"})
    
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
    service: OpenClawService = Depends(get_service)
):
    """
    根据自然语言提示创建新的自动化任务
    
    实现：通过 /tools/invoke 调用相应工具
    - cron.add: 添加定时任务
    - 其他自动化工具调用
    
    参考: [Cron Jobs](23-cron-jobs-and-webhooks)
    """
    logger.info(f"收到创建任务请求: '{request.prompt[:50]}...'")
    
    try:
        logger.info("正在解析任务意图...")
        
        # 使用 Service 层的 create_task 方法，它包含了意图解析和工具调用逻辑
        result = await service.create_task(request.prompt, db)
        
        logger.info(f"任务创建结果: {result}")
        return result
        
    except ValueError as ve:
        logger.warning(f"任务解析失败: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建任务异常: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="任务创建失败")
 
# 通过工具调用方式访问 Gateway 功能
@router.post("/tools/invoke")
async def tools_invoke(
    tool: str,
    args: Dict[str, Any],
    session_key: Optional[str] = None,
    service: OpenClawService = Depends(get_service)
):
    """
    统一工具调用接口
    
    端点对应: /tools/invoke
    参考: [tools-invoke-http.ts](src/gateway/tools-invoke-http.ts#L134-L200)
    """
    result = await service.invoke(tool, args, session_key)
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
    result = await service.chat_completion(
        messages=messages,
        model=model,
        stream=stream
    )
    return result