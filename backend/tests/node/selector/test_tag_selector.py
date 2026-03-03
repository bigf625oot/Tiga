"""
Tests for TagSelector
"""
import pytest
from app.models.node import Node
from app.services.openclaw.node.selector import TagSelector, NodeSelectionError

class TestTagSelector:
    def test_select_exact_match(self):
        node1 = Node(id="1", tags={"type": "gpu"})
        node2 = Node(id="2", tags={"type": "cpu"})
        selector = TagSelector(tags={"type": "gpu"})
        result = selector.select([node1, node2])
        assert result == node1

    def test_select_subset_match(self):
        node1 = Node(id="1", tags={"type": "gpu", "vendor": "nvidia"})
        selector = TagSelector(tags={"type": "gpu"})
        result = selector.select([node1])
        assert result == node1

    def test_select_no_match(self):
        node1 = Node(id="1", tags={"type": "cpu"})
        selector = TagSelector(tags={"type": "gpu"})
        result = selector.select([node1])
        assert result is None

    def test_select_nested_match(self):
        node1 = Node(id="1", tags={"gpu": {"type": "A100", "mem": "80G"}})
        selector = TagSelector(tags={"gpu": {"type": "A100"}})
        result = selector.select([node1])
        assert result == node1

    def test_select_nested_no_match(self):
        node1 = Node(id="1", tags={"gpu": {"type": "A100", "mem": "40G"}})
        selector = TagSelector(tags={"gpu": {"mem": "80G"}})
        result = selector.select([node1])
        assert result is None

    def test_select_empty_list(self):
        selector = TagSelector(tags={"type": "gpu"})
        result = selector.select([])
        assert result is None

    def test_select_none_list(self):
        # Depending on implementation, might return None or raise
        # My implementation returns None for empty/None input if strict check not enforced
        # Wait, I implemented strict check in BaseSelector? No, I commented it out/passed.
        # In TagSelector: `if not nodes: return None`
        selector = TagSelector(tags={"type": "gpu"})
        result = selector.select(None)
        assert result is None

    def test_invalid_tags_init(self):
        with pytest.raises(NodeSelectionError):
            TagSelector(tags="invalid") # type: ignore

    def test_node_tags_none(self):
        node1 = Node(id="1", tags=None)
        selector = TagSelector(tags={"type": "gpu"})
        result = selector.select([node1])
        assert result is None

    def test_node_tags_list(self):
        # Node tags as list (default in model)
        node1 = Node(id="1", tags=["tag1"])
        selector = TagSelector(tags={"tag1": True}) # Won't match list
        result = selector.select([node1])
        assert result is None
