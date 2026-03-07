import sys
import os
from unittest.mock import MagicMock, patch

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../"))
if project_root not in sys.path:
    sys.path.append(project_root)

import unittest
import json
from app.services.pathway.operators.registry import OperatorRegistry
import app.services.pathway.operators.structuring as structuring

class TestStructuringOperator(unittest.TestCase):

    def setUp(self):
        self.mock_table = MagicMock()
        # Mock pathway apply
        self.pw_patcher = patch('app.services.pathway.operators.structuring.pw')
        self.mock_pw = self.pw_patcher.start()
        
        # We need apply to actually run the function if we want to test logic, 
        # but pw.apply runs on columns. 
        # For unit testing the logic inside UDFs, we can extract them or just mock that apply calls with_columns.
        # Here we trust the registration and dispatch mechanics.
        
        self.mock_table.with_columns.return_value = self.mock_table

    def tearDown(self):
        self.pw_patcher.stop()

    def test_json_parse_registration(self):
        op = OperatorRegistry.get_operator("structuring")
        self.assertTrue(callable(op))
        
        config = {
            "action": "json_parse",
            "input_col": "raw_json",
            "output_col": "parsed"
        }
        
        op(self.mock_table, config)
        self.mock_table.with_columns.assert_called()

    def test_csv_parse_dispatch(self):
        op = OperatorRegistry.get_operator("structuring")
        config = {
            "action": "csv_parse",
            "input_col": "raw_csv",
            "output_col": "parsed_row",
            "params": {"delimiter": "|"}
        }
        op(self.mock_table, config)
        self.mock_table.with_columns.assert_called()

if __name__ == '__main__':
    unittest.main()
