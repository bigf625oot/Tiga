"""
网关一致性检查与补偿

处理脏数据检测（校验和不匹配、版本不匹配、乱序）并触发补偿逻辑。
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime
from app.models.node import Node, NodeStatus
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from sqlalchemy import update, select

logger = logging.getLogger("openclaw.gateway.consistency")

class ConsistencyManager:
    """
    管理数据一致性检查和补偿操作。
    """
    def __init__(self):
        self.audit_log: List[Dict[str, Any]] = []
        self.max_audit_log_size = 1000

    async def handle_dirty_data(self, node_id: str, payload: Dict[str, Any]):
        """
        当一致性检查失败时触发。
        1. 将节点标记为STALE/DIRTY。
        2. 记录审计事件。
        3. 触发完全同步。
        """
        logger.warning(f"检测到节点 {node_id} 的脏数据。触发补偿操作。")
        
        # 1. 审计日志
        event = {
            "node_id": node_id,
            "timestamp": datetime.now(),
            "reason": "checksum_mismatch" if payload.get("checksum") else "unknown",
            "payload_snippet": str(payload)[:100]
        }
        self.audit_log.append(event)
        if len(self.audit_log) > self.max_audit_log_size:
            self.audit_log.pop(0)

        # 2. 更新数据库状态
        async with AsyncSessionLocal() as db:
            try:
                await db.execute(
                    update(Node)
                    .where(Node.id == node_id)
                    .values(status=NodeStatus.OFFLINE, error_log=f"于 {datetime.now()} 检测到脏数据")
                )
                await db.commit()
            except Exception as e:
                logger.error(f"更新节点脏数据状态失败: {e}")

        # 3. 触发完全同步命令
        from .ws_handler import ws_manager
        if node_id in ws_manager.active_connections:
            ws = ws_manager.active_connections[node_id]
            try:
                cmd = {
                    "action": "force_sync",
                    "reason": "consistency_check_failed",
                    "timestamp": datetime.now().isoformat()
                }
                await ws.send_json(cmd)
                logger.info(f"已向节点 {node_id} 发送强制同步命令")
            except Exception as e:
                logger.error(f"向节点 {node_id} 发送同步命令失败: {e}")

consistency_manager = ConsistencyManager()