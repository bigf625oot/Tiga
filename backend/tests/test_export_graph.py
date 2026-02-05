import unittest
import os
import shutil
import sqlite3
import yaml
import json
import uuid
import networkx as nx
from pathlib import Path
from backend.scripts.export_graph_data import GraphExporter

class TestGraphExporter(unittest.TestCase):
    def setUp(self):
        # Use unique dir for each test to avoid lock issues
        self.run_id = str(uuid.uuid4())
        self.test_dir = Path(f"./test_export_output_{self.run_id}")
        self.test_dir.mkdir(exist_ok=True)
        
        # Setup SQLite DB
        self.db_path = self.test_dir / "test.db"
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # Create Tables
        self.cursor.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT)")
        self.cursor.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER, amount REAL)")
        
        # Insert Data
        self.cursor.execute("INSERT INTO users VALUES (1, 'Alice', 'alice@example.com')")
        self.cursor.execute("INSERT INTO users VALUES (2, 'Bob', 'bob@example.com')")
        self.cursor.execute("INSERT INTO orders VALUES (101, 1, 100.0)")
        self.cursor.execute("INSERT INTO orders VALUES (102, 2, 200.0)")
        self.conn.commit()
        
        # Create Config
        self.config_path = self.test_dir / "config.yaml"
        self.config_data = {
            "database": {
                "type": "sqlite",
                "database": str(self.db_path)
            },
            "output": {
                "output_dir": str(self.test_dir),
                "update_mode": "overwrite"
            },
            "processing": {
                "chunk_size": 10
            },
            "graph": {
                "entities": [
                    {
                        "table": "users",
                        "id_column": "id",
                        "label": "User",
                        "attributes": ["name"]
                    },
                    {
                        "table": "orders",
                        "id_column": "id",
                        "label": "Order",
                        "attributes": ["amount"]
                    }
                ],
                "relationships": [
                    {
                        "source_table": "orders",
                        "target_table": "users",
                        "foreign_key": "user_id",
                        "relation_type": "PLACED_BY"
                    }
                ]
            }
        }
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config_data, f)
            
    def tearDown(self):
        self.conn.close()
        # Cleanup
        if self.test_dir.exists():
            try:
                shutil.rmtree(self.test_dir)
            except Exception as e:
                print(f"Warning: Failed to cleanup {self.test_dir}: {e}")

    def test_export_and_merge(self):
        # 1. Run Initial Export
        exporter = GraphExporter(str(self.config_path))
        exporter.run()
        
        # Verify GraphML
        graph_path = self.test_dir / "graph_chunk_entity_relation.graphml"
        self.assertTrue(graph_path.exists())
        G = nx.read_graphml(str(graph_path))
        
        # Debug info
        if len(G.nodes) != 4:
            print(f"Nodes found: {G.nodes}")
            for n, d in G.nodes(data=True):
                print(f"  {n}: {d}")
        
        # Check Nodes: 2 Users + 2 Orders = 4
        self.assertEqual(len(G.nodes), 4)
        # Check Edges: 2 Orders linked to Users = 2
        self.assertEqual(len(G.edges), 2)
        
        # Check Properties
        # Note: GraphML keys might be slightly different depending on read/write, 
        # but NetworkX preserves attribute names usually.
        self.assertEqual(G.nodes["User:1"]["name"], "Alice")
        
        # 2. Add New Data to DB
        self.cursor.execute("INSERT INTO users VALUES (3, 'Charlie', 'charlie@example.com')")
        self.cursor.execute("INSERT INTO orders VALUES (103, 3, 300.0)")
        self.conn.commit()
        
        # 3. Update Config to Merge Mode
        self.config_data["output"]["update_mode"] = "merge"
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config_data, f)
            
        # 4. Run Export Again
        exporter = GraphExporter(str(self.config_path))
        exporter.run()
        
        # 5. Verify Merged Graph
        G_merged = nx.read_graphml(str(graph_path))
        
        # Should have 4 + 2 new nodes = 6
        self.assertEqual(len(G_merged.nodes), 6)
        self.assertEqual(len(G_merged.edges), 3)
        
        # Verify old data persists
        self.assertEqual(G_merged.nodes["User:1"]["name"], "Alice")
        # Verify new data exists
        self.assertEqual(G_merged.nodes["User:3"]["name"], "Charlie")
        
        # 6. Idempotency Check (Run again)
        exporter.run()
        G_idempotent = nx.read_graphml(str(graph_path))
        self.assertEqual(len(G_idempotent.nodes), 6)
        self.assertEqual(len(G_idempotent.edges), 3)
        
    def test_property_update(self):
        # 1. Run Initial Export
        exporter = GraphExporter(str(self.config_path))
        exporter.run()
        
        # 2. Modify DB Data (Alice changes name)
        self.cursor.execute("UPDATE users SET name = 'Alice_Updated' WHERE id = 1")
        self.conn.commit()
        
        # 3. Run Merge
        self.config_data["output"]["update_mode"] = "merge"
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config_data, f)
            
        exporter = GraphExporter(str(self.config_path))
        exporter.run()
        
        G = nx.read_graphml(str(self.test_dir / "graph_chunk_entity_relation.graphml"))
        
        # Check if property is updated
        self.assertEqual(G.nodes["User:1"]["name"], "Alice_Updated")

if __name__ == '__main__':
    unittest.main()
