"""
OpenClaw Node Selector Base Module

Defines the base class and interface for node selection strategies.
"""
import abc
from typing import List, Optional, Any, Dict
from app.models.node import Node

class NodeSelectionError(Exception):
    """Raised when node selection fails or encounters an error."""
    pass

class BaseSelector(abc.ABC):
    """
    Abstract base class for node selection strategies.
    """

    @abc.abstractmethod
    def select(self, nodes: List[Node]) -> Optional[Node]:
        """
        Select a node from the given list of nodes.

        Args:
            nodes: A list of available Node instances.

        Returns:
            The selected Node instance, or None if no suitable node is found.
            
        Raises:
            NodeSelectionError: If an error occurs during selection.
        """
        pass

    def _validate_nodes(self, nodes: List[Node]) -> None:
        """
        Validates that the input nodes list is not empty and contains Node instances.

        Args:
            nodes: The list of nodes to validate.

        Raises:
            NodeSelectionError: If validation fails.
        """
        if nodes is None:
             raise NodeSelectionError("Nodes list cannot be None")
        
        # We allow empty list, but if user wants "non-empty" specifically for selection to work,
        # the specific selector might handle empty list by returning None.
        # The prompt says "ensure input non-empty and elements are Node instances".
        # If "non-empty" means len > 0, then we should check length.
        # However, usually select() on empty list returns None.
        # The prompt says: "ensure input non-empty". I will interpret this as "not None".
        # But "ensure input non-empty" usually means `if not nodes: raise`.
        # Let's check if the prompt implies strict validation. 
        # "ensure input non-empty and elements are Node instances"
        # If I enforce len > 0 here, then select([]) raises Error instead of returning None.
        # This might be too strict for a general utility unless intended.
        # But I will follow the instruction "ensure input non-empty".
        
        if not nodes:
             # If the list is empty, we can't select anything. 
             # Does the user want an error or just return None?
             # "ensure input non-empty" suggests raising an error or handling it.
             # Given "NodeSelectionError, convenient for upstream capture", raising seems appropriate if it's considered an error state to call select with no nodes.
             # However, often no nodes available is a valid state returning None.
             # I'll implement strict check as requested, but maybe just log or return None in select?
             # The instruction is under "Provide public utility method: _validate_nodes".
             # So I will implement the check here.
             # I'll assume "non-empty" means "is not None and len > 0".
             # Wait, if I raise Error on empty list, then `select` can't return None for empty list?
             # "select() returns Optional[Node]". If I raise Error, I can't return None.
             # Maybe `_validate_nodes` is just a helper, and `select` calls it?
             # If `select` returns `None` when no matching node is found, it implies valid input but no match.
             # If `nodes` is empty, is that "no match" or "invalid input"?
             # Usually it's "no match".
             # I'll implement `_validate_nodes` to check for `None` and type.
             # For empty list, I'll let it pass or check based on strict interpretation.
             # "ensure input non-empty" -> I will check `if not nodes:` and raise.
             # This means the caller must ensure nodes are available before calling, or handle the error.
             pass

        if not isinstance(nodes, list):
            raise NodeSelectionError("Input must be a list of nodes")

        if not nodes:
             # Strictly following "ensure input non-empty"
             raise NodeSelectionError("Node list cannot be empty")

        for node in nodes:
            if not isinstance(node, Node):
                raise NodeSelectionError(f"Invalid element in nodes list: {type(node)}")
