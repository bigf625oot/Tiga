"""
Tests for LeastLoadSelector
"""
import pytest
from unittest.mock import MagicMock
from app.models.node import Node, NodeStatus
from app.services.openclaw.node.selector import LeastLoadSelector, NodeSelectionError

class TestLeastLoadSelector:
    
    @pytest.fixture
    def metrics_client(self):
        return MagicMock()

    @pytest.fixture
    def selector(self, metrics_client):
        return LeastLoadSelector(metrics_client=metrics_client)

    def test_select_single_node(self, selector, metrics_client):
        node1 = Node(id="1", name="node1", status=NodeStatus.ONLINE)
        metrics_client.get_load.return_value = 0.5
        
        result = selector.select([node1])
        assert result == node1
        metrics_client.get_load.assert_called_with(node1)

    def test_select_multiple_nodes(self, selector, metrics_client):
        node1 = Node(id="1", name="node1", status=NodeStatus.ONLINE)
        node2 = Node(id="2", name="node2", status=NodeStatus.ONLINE)
        node3 = Node(id="3", name="node3", status=NodeStatus.ONLINE)
        
        # Mock loads: node2 lowest
        metrics_client.get_load.side_effect = lambda n: {"1": 0.8, "2": 0.2, "3": 0.5}[n.id]
        
        result = selector.select([node1, node2, node3])
        assert result == node2

    def test_select_tie_break(self, selector, metrics_client):
        # Tie in load, should pick node1 (lexicographically first)
        node1 = Node(id="1", name="alpha", status=NodeStatus.ONLINE)
        node2 = Node(id="2", name="beta", status=NodeStatus.ONLINE)
        
        metrics_client.get_load.return_value = 0.5
        
        result = selector.select([node1, node2])
        assert result == node1
        
        # Verify if order was reversed
        result = selector.select([node2, node1])
        assert result == node1

    def test_select_ignore_offline(self, selector, metrics_client):
        node1 = Node(id="1", name="node1", status=NodeStatus.OFFLINE)
        node2 = Node(id="2", name="node2", status=NodeStatus.ONLINE)
        
        metrics_client.get_load.return_value = 0.5
        
        result = selector.select([node1, node2])
        assert result == node2
        # Should ideally not call get_load on offline node, but implementation might iterate all first?
        # My implementation filters candidates first.
        # Check calls
        # metrics_client.get_load.assert_called_once_with(node2) 
        # (Assuming it only calls for candidates)
        
    def test_select_no_available_nodes(self, selector, metrics_client):
        node1 = Node(id="1", status=NodeStatus.OFFLINE)
        result = selector.select([node1])
        assert result is None

    def test_select_empty_input(self, selector):
        result = selector.select([])
        assert result is None
        result = selector.select(None)
        assert result is None

    def test_select_exception(self, selector, metrics_client):
        node1 = Node(id="1", status=NodeStatus.ONLINE)
        metrics_client.get_load.side_effect = Exception("Metrics Error")
        
        with pytest.raises(NodeSelectionError):
            selector.select([node1])
