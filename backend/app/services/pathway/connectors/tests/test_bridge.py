import sys
import os
from unittest.mock import MagicMock, patch

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../"))
if project_root not in sys.path:
    sys.path.append(project_root)

import unittest
from app.services.pathway.connectors.bridge import DataSourceBridge
from app.models.data_source import DataSource

class TestDataSourceBridge(unittest.TestCase):

    def setUp(self):
        self.bridge = DataSourceBridge()
        
        # Patch the SessionLocal defined in bridge.py, not the one in db.session
        self.session_patcher = patch('app.services.pathway.connectors.bridge.SessionLocal')
        self.MockSession = self.session_patcher.start()
        self.mock_db = self.MockSession.return_value
        
        # Patch decrypt_field
        self.decrypt_patcher = patch('app.services.pathway.connectors.bridge.decrypt_field')
        self.mock_decrypt = self.decrypt_patcher.start()
        self.mock_decrypt.side_effect = lambda x: f"decrypted_{x}"
        
        # Patch settings
        self.settings_patcher = patch('app.services.pathway.connectors.bridge.settings')
        self.mock_settings = self.settings_patcher.start()
        self.mock_settings.database_url = "sqlite:///test.db"

    def tearDown(self):
        self.session_patcher.stop()
        self.decrypt_patcher.stop()
        self.settings_patcher.stop()

    def test_get_source_config_mysql(self):
        # Mock DB response
        mock_source = DataSource(
            id=1,
            name="Test MySQL",
            type="mysql",
            host="localhost",
            port=3306,
            username="root",
            password_encrypted="secret",
            database="testdb",
            config={"table_name": "users"}
        )
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_source
        
        config = self.bridge.get_source_config(1)
        
        # Verify
        self.assertIn("connection_string", config)
        self.assertIn("mysql+pymysql://root:decrypted_secret@localhost:3306/testdb", config["connection_string"])
        self.assertEqual(config["table_name"], "users")

    def test_get_source_config_api(self):
        mock_source = DataSource(
            id=2,
            name="Test API",
            type="api",
            url="https://api.example.com/v1",
            encrypted_token="token123",
            config={"headers": {"Accept": "application/json"}}
        )
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_source
        
        config = self.bridge.get_source_config(2)
        
        self.assertEqual(config["url"], "https://api.example.com/v1")
        self.assertIn("headers", config)
        self.assertEqual(config["headers"]["Authorization"], "Bearer decrypted_token123")

if __name__ == '__main__':
    unittest.main()
