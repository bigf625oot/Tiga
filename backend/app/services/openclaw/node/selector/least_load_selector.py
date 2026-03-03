"""
OpenClaw Node Least Load Selector

Selects the node with the minimum load.
"""
from typing import List, Optional, Protocol, Any
from app.models.node import Node, NodeStatus
from .base import BaseSelector, NodeSelectionError

class MetricsClient(Protocol):
    """Protocol for metrics client to fetch node load."""
    def get_load(self, node: Node) -> float:
        """Returns the load of the given node."""
        ...

class LeastLoadSelector(BaseSelector):
    """
    Selects the node with the least load among available nodes.
    Only considers nodes with status 'Ready' (or equivalent).
    """

    def __init__(self, metrics_client: MetricsClient):
        """
        Initialize with a metrics client.

        Args:
            metrics_client: An instance capable of retrieving node load.
        """
        self.metrics_client = metrics_client

    def select(self, nodes: List[Node]) -> Optional[Node]:
        """
        Select the node with the lowest load.
        
        Ties are broken by node name lexicographically.
        Only considers nodes with status NodeStatus.ONLINE (assuming Ready maps to ONLINE).
        
        Args:
            nodes: List of candidate nodes.
            
        Returns:
            The selected Node, or None if no suitable node is found.
        """
        # Validate input using base method if needed, but let's handle empty list gracefully
        if not nodes:
            return None
            
        candidates = []
        for node in nodes:
            # Check if node is ready/online
            # The prompt says "node status for Ready". The NodeStatus enum has ONLINE.
            # I will assume "Ready" means ONLINE.
            if node.status == NodeStatus.ONLINE or node.status == "ready": # Handle both just in case
                candidates.append(node)
        
        if not candidates:
            return None
            
        # Sort by load (asc), then name (asc)
        # We need to fetch load for each candidate.
        # Note: This might be slow if get_load is slow. But benchmark requirement is < 5ms for 1k nodes.
        # This implies get_load must be fast (e.g. cached or local lookup).
        
        try:
            # Create a list of (load, name, node) tuples for sorting
            load_data = []
            for node in candidates:
                load = self.metrics_client.get_load(node)
                # Ensure name is not None for sorting
                name = node.name or "" 
                load_data.append((load, name, node))
            
            # Sort: primary key load, secondary key name
            load_data.sort(key=lambda x: (x[0], x[1]))
            
            return load_data[0][2]
            
        except Exception as e:
            raise NodeSelectionError(f"Error during least load selection: {e}")
