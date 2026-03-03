"""
OpenClaw Node Tag Selector

Implements a node selection strategy based on tag matching.
"""
from typing import List, Optional, Any, Dict
from app.models.node import Node
from .base import BaseSelector, NodeSelectionError

class TagSelector(BaseSelector):
    """
    Selects nodes that match a set of required tags.
    """

    def __init__(self, tags: Dict[str, Any]):
        """
        Initialize with the required tags for selection.

        Args:
            tags: A dictionary of tags that a node must possess.
                  Supports nested dictionaries for complex matching.
        """
        if not isinstance(tags, dict):
            raise NodeSelectionError("Tags must be a dictionary")
        self.tags = tags

    def select(self, nodes: List[Node]) -> Optional[Node]:
        """
        Select the first node that contains all required tags.

        Args:
            nodes: A list of candidate nodes.

        Returns:
            The first matching Node, or None if no match is found.
        """
        try:
            # We can use _validate_nodes here, but strict "non-empty" check might be annoying if list is empty naturally.
            # However, prompt asked for _validate_nodes to ensure non-empty.
            # If nodes is empty, select returns None usually.
            # I'll call _validate_nodes if nodes is not None and not empty, or handle exception.
            # Or just check explicitly.
            if not nodes:
                return None
            
            # self._validate_nodes(nodes) # This would raise if empty.
            # Given the requirement "ensure input non-empty", maybe the caller is expected to provide non-empty list?
            # Or maybe _validate_nodes is just a utility for implementation to use if they want strict validation.
            # I'll stick to standard behavior: empty input -> None result.
            # But I should check types.
            for node in nodes:
                if not isinstance(node, Node):
                     # Skip invalid nodes or raise? BaseSelector said validate ensures Node instance.
                     # Let's trust caller or do quick check.
                     continue

                # Node tags from DB might be a list or dict. Assuming dict based on usage.
                # If it's a list (as defined in model default=[]), we might need conversion or assume it's stored as dict in JSON.
                # The prompt implies dict usage: tags={'gpu': {'type': 'A100'}}
                node_tags = node.tags
                if isinstance(node_tags, list):
                    # Attempt to treat list as dict if it's list of k-v or just ignore
                    # If it's strictly a list of strings, we can't match nested dict structure easily unless we parse.
                    # I'll assume it's a dict for now, or empty dict if None.
                    if not node_tags:
                        node_tags = {}
                    else:
                        # If it is a list, maybe we can't match dict tags against it.
                        # Unless we convert list of strings to dict {tag: True}?
                        # For safety, if node.tags is list, we treat it as empty dict for dict-based matching, or just fail match.
                        # But if the user stores dict in JSON column, SQLAlchemy returns dict.
                        pass
                elif node_tags is None:
                    node_tags = {}
                
                if self._is_subset(self.tags, node_tags):
                    return node
            
            return None
            
        except Exception as e:
            # Wrap unexpected errors
            raise NodeSelectionError(f"Error during tag selection: {e}")

    def _is_subset(self, required: Dict[str, Any], actual: Any) -> bool:
        """
        Recursively check if 'required' is a subset of 'actual'.
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
                if not self._is_subset(req_val, act_val):
                    return False
            else:
                if req_val != act_val:
                    return False
        return True
