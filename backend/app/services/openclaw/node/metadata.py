"""
OpenClaw Node Metadata Management

负责管理节点的硬件信息、环境标签和状态元数据。
支持基于标签的节点筛选和查询。
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.node import Node
from app.core.logger import logger

class NodeMetadataManager:
    
    @staticmethod
    async def update_node_metadata(db: AsyncSession, node_id: str, metadata: Dict[str, Any]):
        """
        更新节点的元数据（硬件信息、标签等）。
        
        Args:
            db: 数据库会话
            node_id: 节点ID
            metadata: 元数据字典，可能包含:
                - resources: {cpu: {cores: int, model: str}, memory: {total: int}, gpu: ...}
                - tags: Dict[str, Any] (自定义标签, 如 environment, plugins)
                - location: {country: str, region: str} (IP归属地)
        """
        try:
            result = await db.execute(select(Node).filter(Node.id == node_id))
            node = result.scalars().first()
            
            if not node:
                logger.warning(f"Node {node_id} not found for metadata update")
                return

            # Update Tags
            if "tags" in metadata:
                # Merge or replace? Usually replace is safer to avoid stale tags, 
                # but let's assume 'tags' in metadata is the full current set.
                # However, we should preserve existing tags if not provided?
                # For now, let's update with provided tags.
                current_tags = node.tags or {}
                if isinstance(current_tags, list):
                     # Handle legacy list format if any
                     current_tags = {t: True for t in current_tags}
                
                new_tags = metadata["tags"]
                if isinstance(new_tags, dict):
                    current_tags.update(new_tags)
                    node.tags = current_tags
                
            # Update Hardware/Resources info into 'config' field
            if "resources" in metadata:
                current_config = node.config or {}
                current_config["resources"] = metadata["resources"]
                node.config = current_config
            
            # Update Location info into 'config' or dedicated fields if we had them
            if "location" in metadata:
                current_config = node.config or {}
                current_config["location"] = metadata["location"]
                node.config = current_config

            await db.commit()
            logger.info(f"Updated metadata for node {node_id}")
            
        except Exception as e:
            logger.error(f"Failed to update node metadata: {e}")
            await db.rollback()

    @staticmethod
    async def filter_nodes_by_tags(db: AsyncSession, tags: Dict[str, Any]) -> List[Node]:
        """
        根据标签筛选节点。
        使用 TagSelector 逻辑，但这里是数据库查询层面的封装（如果支持 JSON 查询）。
        由于数据库 JSON 查询复杂且依赖具体 DB (PG vs SQLite)，这里先获取所有在线节点再内存过滤。
        """
        # 1. Get all online nodes
        # TODO: Optimize with DB-specific JSON query if possible
        from app.models.node import NodeStatus
        result = await db.execute(select(Node).filter(Node.status == NodeStatus.ONLINE))
        nodes = result.scalars().all()
        
        # 2. Use TagSelector for filtering
        from app.services.openclaw.node.selector import TagSelector
        
        # TagSelector expects a list and returns a single node (select one).
        # We need a method to return ALL matching nodes.
        # Let's implement a simple filter here or extend TagSelector.
        
        matching_nodes = []
        selector = TagSelector(tags) # Reuse logic for checking subset
        
        for node in nodes:
            # We can use the internal helper _is_subset from TagSelector if we make it public or duplicate logic.
            # Or just duplicate logic for now to avoid protected access.
            node_tags = node.tags or {}
            if isinstance(node_tags, list):
                node_tags = {t: True for t in node_tags}
                
            if NodeMetadataManager._is_subset(tags, node_tags):
                matching_nodes.append(node)
                
        return matching_nodes

    @staticmethod
    def _is_subset(required: Dict[str, Any], actual: Any) -> bool:
        """
        Recursively check if 'required' is a subset of 'actual'.
        (Duplicated from TagSelector for utility)
        """
        if not isinstance(actual, dict):
            return False
            
        for key, value in required.items():
            if key not in actual:
                return False
            
            req_val = value
            act_val = actual[key]
            
            if isinstance(req_val, dict):
                if not isinstance(act_val, dict):
                    return False
                if not NodeMetadataManager._is_subset(req_val, act_val):
                    return False
            else:
                if req_val != act_val:
                    return False
        return True

node_metadata_manager = NodeMetadataManager()
