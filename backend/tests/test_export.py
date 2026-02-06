import unittest
import sys
import os

# Add root directory to sys.path to allow importing from scripts
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from scripts.export_graph_data import process_chunk


class TestGraphExport(unittest.TestCase):
    def test_process_chunk(self):
        # Mock Data
        data = {"id": [1, 2], "name": ["Alice", "Bob"], "bio": ["Loves coding", "Loves hiking"], "dept_id": [101, 102]}
        df = pd.DataFrame(data)

        table_config = {
            "table": "employees",
            "label": "Employee",
            "id_column": "id",
            "attributes": ["name"],
            "long_text_fields": ["bio"],
        }

        relationships = [
            {
                "source_table": "employees",
                "target_table": "departments",
                "target_label": "Department",
                "foreign_key": "dept_id",
                "relation_type": "WORKS_IN",
            }
        ]

        # Run
        result = process_chunk(df, table_config, relationships, batch_id=1)

        # Verify Nodes
        self.assertEqual(len(result["nodes"]), 2)
        self.assertEqual(result["nodes"][0]["id"], "Employee:1")
        self.assertEqual(result["nodes"][0]["properties"]["name"], "Alice")
        self.assertNotIn("bio", result["nodes"][0]["properties"])  # bio should be in mapping

        # Verify Mappings (Vector DB)
        self.assertEqual(len(result["mappings"]), 2)
        self.assertEqual(result["mappings"][0]["node_id"], "Employee:1")
        self.assertEqual(result["mappings"][0]["vector_id"], "Employee:1_bio")

        # Verify Edges
        self.assertEqual(len(result["edges"]), 2)
        self.assertEqual(result["edges"][0]["source"], "Employee:1")
        self.assertEqual(result["edges"][0]["target"], "Department:101")
        self.assertEqual(result["edges"][0]["relation"], "WORKS_IN")


if __name__ == "__main__":
    unittest.main()
