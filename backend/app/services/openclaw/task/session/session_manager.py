"""
OpenClaw Task Session Management

核心概念：TaskSession
- 维护 session_id -> node_id 的映射
- 管理 Session 生命周期 (TTL)
- 提供亲和性重选策略 (Affinity Re-selection)
"""

import uuid
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
import asyncio

# Using simple in-memory cache for now. In production, use Redis.
# Structure: {session_id: {"node_id": str, "updated_at": datetime, "metadata": dict}}
_SESSION_CACHE: Dict[str, Dict[str, Any]] = {}
_SESSION_TTL = timedelta(hours=24)
_SESSION_TIMEOUT = timedelta(minutes=15) # Runtime session timeout

logger = logging.getLogger("openclaw.task.session")

class TaskSessionManager:
    """
    Manages task sessions and node affinity.
    """

    @staticmethod
    def generate_session_id() -> str:
        """Generate a globally unique session ID (UUID v4)."""
        return str(uuid.uuid4())

    @staticmethod
    def register_session(session_id: str, node_id: str, metadata: Dict[str, Any] = None):
        """
        Register or update a session mapping.
        """
        _SESSION_CACHE[session_id] = {
            "node_id": node_id,
            "updated_at": datetime.now(),
            "metadata": metadata or {}
        }
        logger.info(f"Registered session {session_id} -> {node_id}")

    @staticmethod
    def get_affinity_node(session_id: str) -> Optional[str]:
        """
        Get the preferred node for a session.
        Returns None if session expired or not found.
        """
        if session_id not in _SESSION_CACHE:
            return None
            
        entry = _SESSION_CACHE[session_id]
        if datetime.now() - entry["updated_at"] > _SESSION_TTL:
            del _SESSION_CACHE[session_id]
            return None
            
        return entry["node_id"]

    @staticmethod
    async def reselect_affinity_node(session_id: str, exclude_node_id: str, candidates: List[Any]) -> Optional[str]:
        """
        Trigger 'Affinity Re-selection' strategy.
        Selects a new node from candidates based on:
        1. Same Availability Zone (if location info available)
        2. Same Version
        3. Least Load
        
        Args:
            session_id: The session ID needing reassignment.
            exclude_node_id: The node that failed or is unavailable.
            candidates: List of available Node objects.
            
        Returns:
            The new node_id, or None if no suitable candidate.
        """
        if not candidates:
            return None

        # Filter out the excluded node
        valid_candidates = [n for n in candidates if n.id != exclude_node_id]
        
        if not valid_candidates:
            return None

        # Get session metadata to match affinity (e.g., version, location)
        session_info = _SESSION_CACHE.get(session_id, {})
        original_meta = session_info.get("metadata", {})
        
        # 1. Filter by Version (if recorded)
        target_version = original_meta.get("version")
        if target_version:
            same_version_nodes = [n for n in valid_candidates if n.version == target_version]
            if same_version_nodes:
                valid_candidates = same_version_nodes
        
        # 2. Filter by Location/Zone (if recorded)
        # Assuming node.config['location'] exists
        target_location = original_meta.get("location")
        if target_location:
             # Logic to match location
             pass

        # 3. Least Load (Sort by load)
        # Using metrics client or direct attribute if available. 
        # For now, reusing LeastLoadSelector logic concept: sort by some metric.
        # Assuming DispatchService has access to load metrics or we just pick random/first for now 
        # if we don't inject MetricsClient here.
        # Let's assume we pick the first one from filtered list (simplified least load).
        
        new_node = valid_candidates[0]
        
        # Update mapping
        TaskSessionManager.register_session(session_id, new_node.id, original_meta)
        logger.info(f"Re-selected affinity node for session {session_id}: {exclude_node_id} -> {new_node.id}")
        
        return new_node.id

    # Lifecycle Hooks
    @staticmethod
    async def on_create(session_id: str, context: Dict[str, Any]):
        """Hook called when a new session is created."""
        logger.info(f"Session created: {session_id}")

    @staticmethod
    async def on_reuse(session_id: str, node_id: str):
        """Hook called when a session is reused."""
        logger.info(f"Session reused: {session_id} on {node_id}")

    @staticmethod
    async def on_destroy(session_id: str):
        """Hook called when a session is destroyed/expired."""
        if session_id in _SESSION_CACHE:
            del _SESSION_CACHE[session_id]
        logger.info(f"Session destroyed: {session_id}")

# Export singleton or class
task_session_manager = TaskSessionManager
