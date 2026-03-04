"""
应用场景：
    负责节点的发现与状态查询。
    
核心功能：
    - 节点在线状态检查（优先缓存，回退数据库）
    - 节点状态缓存更新

__author__ = "xucao"
"""

import json
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.redis import get_redis_connection
from app.models.node import Node, NodeStatus
from app.core.logger import logger

class NodeDiscoveryService:
    """节点发现与状态检查服务"""

    @staticmethod
    async def get_node_status(node_id: str, db: AsyncSession) -> Dict[str, Any]:
        """
        获取节点在线状态
        1. 优先从 Redis 缓存获取
        2. 缓存未命中或状态未知，从数据库查询
        
        Returns:
            {
                "status": "online" | "offline" | "unknown",
                "last_heartbeat": datetime,
                "update_time": datetime
            }
        """
        redis_key = f"node:status:{node_id}"
        
        # 1. 尝试从 Redis 获取
        try:
            redis_client = await get_redis_connection()
            cached_status = await redis_client.get(redis_key)
            
            if cached_status:
                status_data = json.loads(cached_status)
                status = status_data.get("status")
                
                if status and status != "unknown":
                    # 检查数据新鲜度，例如超过 5 分钟视为过期
                    update_ts = status_data.get("update_time_ts")
                    if update_ts and (datetime.utcnow().timestamp() - update_ts) < 300:
                         return {
                            "status": status,
                            "last_heartbeat": datetime.fromtimestamp(status_data.get("last_heartbeat_ts", 0)),
                            "update_time": datetime.fromtimestamp(update_ts)
                        }
        except Exception as e:
            logger.warning(f"Redis get node status failed: {e}")

        # 2. 回退到数据库查询
        try:
            stmt = select(Node).where(Node.id == node_id)
            result = await db.execute(stmt)
            node = result.scalars().first()
            
            status = "unknown"
            last_heartbeat = None
            
            if node:
                status = "online" if node.status == NodeStatus.ONLINE else "offline"
                last_heartbeat = node.last_heartbeat
            
            # 更新缓存
            try:
                redis_client = await get_redis_connection()
                now_ts = datetime.utcnow().timestamp()
                cache_data = {
                    "status": status,
                    "last_heartbeat_ts": last_heartbeat.timestamp() if last_heartbeat else 0,
                    "update_time_ts": now_ts
                }
                await redis_client.setex(redis_key, 300, json.dumps(cache_data))
            except Exception as e:
                logger.warning(f"Redis set node status failed: {e}")
                
            return {
                "status": status,
                "last_heartbeat": last_heartbeat,
                "update_time": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"DB get node status failed: {e}")
            return {"status": "unknown", "error": str(e)}

    @staticmethod
    async def update_node_status_cache(node_id: str, status: str, last_heartbeat: datetime):
        """主动更新节点状态缓存"""
        redis_key = f"node:status:{node_id}"
        try:
            redis_client = await get_redis_connection()
            now_ts = datetime.utcnow().timestamp()
            cache_data = {
                "status": status,
                "last_heartbeat_ts": last_heartbeat.timestamp() if last_heartbeat else 0,
                "update_time_ts": now_ts
            }
            await redis_client.setex(redis_key, 300, json.dumps(cache_data))
        except Exception as e:
            logger.warning(f"Redis update node status failed: {e}")
