
import os
import tempfile
import networkx as nx
import unittest
from unittest.mock import MagicMock, patch
from app.services.relation_fix_service import RelationFixService

class TestRelationFixServiceNoneType(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.graph_path = os.path.join(self.test_dir, "test_graph.graphml")
        self.backup_dir = os.path.join(self.test_dir, "backups")
        self.log_file = os.path.join(self.test_dir, "test.log")
        
        # Initialize an empty graph
        G = nx.Graph()
        nx.write_graphml(G, self.graph_path)
        
        # Initialize service with patched paths
        self.service = RelationFixService()
        self.service.graph_path = self.graph_path
        self.service.backup_dir = self.backup_dir
        self.service.log_file = self.log_file
        
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir)

    def test_apply_fix_with_none_attributes(self):
        fixes = [
            {
                "source": "NodeA",
                "target": "NodeB",
                "description": "Test Relation",
                "attributes": {
                    "valid_attr": "value",
                    "none_attr": None,
                    "int_attr": 123
                }
            }
        ]
        
        count = self.service.apply_fix(fixes)
        self.assertEqual(count, 1)
        
        # Verify graph content
        G = nx.read_graphml(self.graph_path)
        self.assertTrue(G.has_edge("NodeA", "NodeB"))
        edge_data = G.get_edge_data("NodeA", "NodeB")
        
        self.assertEqual(edge_data.get("valid_attr"), "value")
        self.assertEqual(edge_data.get("int_attr"), 123)
        self.assertNotIn("none_attr", edge_data) # None attribute should be skipped

    def test_create_relation_with_none_attributes(self):
        source = "NodeC"
        target = "NodeD"
        rel_type = "related"
        attributes = {
            "comment": "This is a test",
            "metadata": None, # Should be skipped
            "score": 0.95
        }
        
        success = self.service.create_relation(source, target, rel_type, attributes)
        self.assertTrue(success)
        
        # Verify graph content
        G = nx.read_graphml(self.graph_path)
        self.assertTrue(G.has_edge(source, target))
        edge_data = G.get_edge_data(source, target)
        
        self.assertEqual(edge_data.get("comment"), "This is a test")
        self.assertEqual(edge_data.get("score"), 0.95)
        self.assertNotIn("metadata", edge_data)

if __name__ == "__main__":
    unittest.main()
