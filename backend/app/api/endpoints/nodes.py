import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.node import Node, NodeCreate, NodeUpdate, NodeMetricCreate, Alert, CommandRequest
from app.services.openclaw.node_manager import node_manager

# 初始化日志记录器
logger = logging.getLogger("openclaw.nodes")

router = APIRouter()

@router.get("/", response_model=List[Node])
async def list_nodes(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """
    获取所有节点列表。
    """
    logger.info(f"正在查询节点列表: skip={skip}, limit={limit}")
    nodes = await node_manager.get_nodes(db, skip=skip, limit=limit)
    logger.info(f"节点查询完成，共获取到 {len(nodes)} 个节点")
    return nodes

@router.post("/register", response_model=Node)
async def register_node(node_in: NodeCreate, db: AsyncSession = Depends(get_db)):
    """
    注册一个新节点。
    """
    logger.info(f"收到节点注册请求: 名称={node_in.name}, 分组={node_in.group}")
    try:
        node = await node_manager.register_node(db, node_in)
        logger.info(f"节点注册成功: ID={node.id}, 状态={node.status}")
        return node
    except Exception as e:
        logger.error(f"节点注册失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="注册节点时发生内部错误")

@router.get("/{node_id}", response_model=Node)
async def get_node(node_id: str, db: AsyncSession = Depends(get_db)):
    """
    根据 ID 获取节点详情。
    """
    logger.debug(f"正在获取节点详情: ID={node_id}")
    node = await node_manager.get_node(db, node_id)
    if not node:
        logger.warning(f"获取节点失败: 未找到 ID 为 {node_id} 的节点")
        raise HTTPException(status_code=404, detail="未找到该节点")
    return node

@router.post("/{node_id}/heartbeat", response_model=Node)
async def heartbeat(
    node_id: str, 
    metrics: Optional[NodeMetricCreate] = None, 
    db: AsyncSession = Depends(get_db)
):
    """
    接收节点心跳，可选择性携带监控指标。
    """
    logger.debug(f"收到节点心跳: ID={node_id}, 包含指标: {metrics is not None}")
    node = await node_manager.heartbeat(db, node_id, metrics)
    if not node:
        logger.warning(f"心跳处理失败: 节点 {node_id} 未在系统中注册")
        raise HTTPException(status_code=404, detail="节点未找到")
    return node

@router.post("/sync")
async def sync_nodes(db: AsyncSession = Depends(get_db)):
    """
    手动触发从 OpenClaw Gateway 同步。
    """
    logger.info("开始执行节点手动同步流程...")
    try:
        await node_manager.sync_from_gateway(db)
        logger.info("节点同步完成")
        return {"status": "synced", "message": "同步成功"}
    except Exception as e:
        logger.error(f"节点同步过程中发生异常: {str(e)}")
        raise HTTPException(status_code=500, detail="同步失败")

@router.post("/check_health")
async def check_health(db: AsyncSession = Depends(get_db)):
    """
    手动触发健康检查（将超时节点标记为离线）。
    """
    logger.info("启动全局节点健康检查...")
    await node_manager.check_nodes_health(db)
    logger.info("健康检查任务执行完毕")
    return {"status": "checked", "message": "健康检查已执行"}

@router.patch("/{node_id}/group", response_model=Node)
async def update_node_group(
    node_id: str, 
    group: str = Query(..., description="新分组名称"), 
    db: AsyncSession = Depends(get_db)
):
    """
    更新节点分组。
    """
    logger.info(f"请求修改节点分组: ID={node_id}, 目标新分组={group}")
    node = await node_manager.update_node_group(db, node_id, group)
    if not node:
        logger.error(f"修改分组失败: 节点 {node_id} 不存在")
        raise HTTPException(status_code=404, detail="节点不存在")
    logger.info(f"节点 {node_id} 分组已成功修改为 {group}")
    return node

@router.post("/{node_id}/tags", response_model=Node)
async def add_node_tag(
    node_id: str, 
    tag: str = Query(..., description="要添加的标签"), 
    db: AsyncSession = Depends(get_db)
):
    """
    为节点添加标签。
    """
    logger.info(f"尝试为节点 {node_id} 添加标签: {tag}")
    node = await node_manager.get_node(db, node_id)
    if not node:
        logger.warning(f"添加标签失败: 节点 {node_id} 不存在")
        raise HTTPException(status_code=404, detail="节点不存在")
    
    current_tags = node.tags or []
    if tag not in current_tags:
        current_tags.append(tag)
        await node_manager.update_node_tags(db, node_id, current_tags)
        logger.info(f"节点 {node_id} 标签已更新: {current_tags}")
    else:
        logger.debug(f"节点 {node_id} 已存在标签 {tag}，跳过操作")
    
    return node

@router.delete("/{node_id}/tags/{tag}", response_model=Node)
async def remove_node_tag(
    node_id: str, 
    tag: str, 
    db: AsyncSession = Depends(get_db)
):
    """
    移除节点标签。
    """
    logger.info(f"尝试从节点 {node_id} 移除标签: {tag}")
    node = await node_manager.get_node(db, node_id)
    if not node:
        logger.warning(f"移除标签失败: 节点 {node_id} 不存在")
        raise HTTPException(status_code=404, detail="节点不存在")
    
    current_tags = node.tags or []
    if tag in current_tags:
        current_tags.remove(tag)
        await node_manager.update_node_tags(db, node_id, current_tags)
        logger.info(f"节点 {node_id} 标签已移除，剩余: {current_tags}")
    else:
        logger.warning(f"节点 {node_id} 原本就不包含标签: {tag}")
    
    return node

@router.post("/command", response_model=Dict[str, Any])
async def dispatch_command(
    request: CommandRequest, 
    db: AsyncSession = Depends(get_db)
):
    """
    向多个节点分发指令。
    """
    logger.info(f"开始指令分发任务: 指令={request.command}, 目标范围(节点数)={len(request.target_nodes) if request.target_nodes else '按分组/标签'}")
    try:
        result = await node_manager.dispatch_command(
            db, 
            command=request.command, 
            params=request.params, 
            target_nodes=request.target_nodes, 
            target_group=request.target_group, 
            target_tags=request.target_tags
        )
        logger.info(f"指令分发完成: {result.get('success_count', 0)} 成功, {result.get('fail_count', 0)} 失败")
        return result
    except Exception as e:
        logger.error(f"指令分发任务执行出错: {str(e)}")
        raise HTTPException(status_code=500, detail="指令下发失败")