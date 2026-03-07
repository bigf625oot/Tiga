import sys
import os
from unittest.mock import MagicMock, patch

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../"))
if project_root not in sys.path:
    sys.path.append(project_root)

import unittest
from app.services.pathway.core.models import DAGPipeline, DAGNode
from app.services.pathway.core.parser import DAGParser
from app.services.pathway.core.exceptions import ConfigurationError

class TestDAGParser(unittest.TestCase):

    def setUp(self):
        self.parser = DAGParser()
        
        # Mock connectors and registry
        self.source_patcher = patch('app.services.pathway.core.parser.get_source')
        self.mock_get_source = self.source_patcher.start()
        
        self.sink_patcher = patch('app.services.pathway.core.parser.get_sink')
        self.mock_get_sink = self.sink_patcher.start()
        
        self.registry_patcher = patch('app.services.pathway.core.parser.OperatorRegistry')
        self.mock_registry = self.registry_patcher.start()
        
        # Mock Table
        self.mock_table = MagicMock()
        self.mock_get_source.return_value.read.return_value = self.mock_table
        self.mock_registry.get_operator.return_value.return_value = self.mock_table
        
        # For union
        self.mock_table.__add__.return_value = self.mock_table

    def tearDown(self):
        self.source_patcher.stop()
        self.sink_patcher.stop()
        self.registry_patcher.stop()

    def test_linear_pipeline(self):
        # A -> B -> C
        pipeline = DAGPipeline(
            id="pipe1",
            name="Linear",
            nodes=[
                DAGNode(id="A", type="source", operator="kafka", config={}),
                DAGNode(id="B", type="transform", operator="text_process", config={}, inputs=["A"]),
                DAGNode(id="C", type="sink", operator="redis", config={}, inputs=["B"])
            ]
        )
        
        self.parser.parse(pipeline)
        
        # Check source read called
        self.mock_get_source.assert_called_with("kafka")
        # Check transform called
        self.mock_registry.get_operator.assert_called_with("text_process")
        # Check sink write called
        self.mock_get_sink.assert_called_with("redis")

    def test_union_combiner(self):
        # A, B -> Union -> C
        pipeline = DAGPipeline(
            id="pipe2",
            name="Union",
            nodes=[
                DAGNode(id="A", type="source", operator="kafka", config={}),
                DAGNode(id="B", type="source", operator="s3", config={}),
                DAGNode(id="U", type="combiner", operator="union", config={}, inputs=["A", "B"]),
                DAGNode(id="C", type="sink", operator="redis", config={}, inputs=["U"])
            ]
        )
        
        self.parser.parse(pipeline)
        
        # Verify A and B tables were added
        # Since we use mock_table for everything, result of A+B is mock_table
        # Just ensure parse completes without error
        self.assertIn("U", self.parser.tables)

    def test_cycle_detection(self):
        # A -> B -> A
        pipeline = DAGPipeline(
            id="pipe3",
            name="Cycle",
            nodes=[
                DAGNode(id="A", type="transform", operator="op", config={}, inputs=["B"]),
                DAGNode(id="B", type="transform", operator="op", config={}, inputs=["A"])
            ]
        )
        
        with self.assertRaises(ConfigurationError):
            self.parser.parse(pipeline)

    def test_missing_input(self):
        # A (missing) -> B
        pipeline = DAGPipeline(
            id="pipe4",
            name="Missing",
            nodes=[
                DAGNode(id="B", type="transform", operator="op", config={}, inputs=["A"])
            ]
        )
        
        # This might fail at sort or processing depending on implementation
        # Our sort checks node existence if referenced? 
        # Actually our sort implementation iterates nodes. inputs are just IDs.
        # If A is not in nodes list, visit(A) will fail?
        # Let's check sort logic: visit(input_id) -> node_map.get(input_id) -> raises if None
        
        with self.assertRaises(ConfigurationError):
            self.parser.parse(pipeline)

if __name__ == '__main__':
    unittest.main()
