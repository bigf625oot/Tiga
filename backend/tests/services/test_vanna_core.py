
import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
from app.services.data.vanna.core import VannaCore

class TestVannaCore(unittest.TestCase):
    def setUp(self):
        # Mock dependencies
        self.mock_lancedb = patch('app.services.data.vanna.core.lancedb').start()
        # Mock OpenAI class itself to prevent instantiation errors during configure_llm
        self.mock_openai_class = patch('app.services.data.vanna.core.OpenAI').start()
        
        # Initialize VannaCore with mocks
        self.vanna = VannaCore()
        # Manually set a mock client to simulate configured state for existing tests
        self.vanna.openai_client = MagicMock()

    def tearDown(self):
        patch.stopall()

    def test_configure_llm(self):
        # Test configuration
        self.vanna.openai_client = None # Reset
        self.vanna.configure_llm("sk-test", "http://test", "gpt-4")
        
        self.assertIsNotNone(self.vanna.openai_client)
        self.assertEqual(self.vanna.model, "gpt-4")
        self.mock_openai_class.assert_called_with(api_key="sk-test", base_url="http://test")

    def test_check_llm_configured(self):
        self.vanna.openai_client = None
        with self.assertRaises(RuntimeError):
            self.vanna._check_llm_configured()

    def test_classify_intent(self):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "aggregation"
        self.vanna.openai_client.chat.completions.create.return_value = mock_response
        
        intent = self.vanna.classify_intent("How many users are there?")
        self.assertEqual(intent, "aggregation")

    def test_generate_sql_caching(self):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "SELECT count(*) FROM users"
        self.vanna.openai_client.chat.completions.create.return_value = mock_response
        
        # Mock get_related_context to avoid embedding call
        self.vanna.get_related_context = MagicMock(return_value=["context"])

        # First call - should trigger LLM
        sql1 = self.vanna.generate_sql("count users")
        self.assertEqual(sql1, "SELECT count(*) FROM users")
        self.assertEqual(self.vanna.openai_client.chat.completions.create.call_count, 1)

        # Second call - should hit cache
        sql2 = self.vanna.generate_sql("count users")
        self.assertEqual(sql2, "SELECT count(*) FROM users")
        self.assertEqual(self.vanna.openai_client.chat.completions.create.call_count, 1) # Count should remain 1

    def test_mask_sensitive_data(self):
        df = pd.DataFrame({
            'name': ['Alice', 'Bob'],
            'email': ['alice@example.com', 'bob.jones@work.org'],
            'phone': ['13812345678', '15987654321'],
            'other': ['foo', 'bar']
        })
        
        masked_df = self.vanna._mask_sensitive_data(df)
        
        # Check Email Masking
        self.assertEqual(masked_df['email'][0], 'al***@example.com')
        self.assertEqual(masked_df['email'][1], 'bo***@work.org')
        
        # Check Phone Masking
        self.assertEqual(masked_df['phone'][0], '138****5678')
        self.assertEqual(masked_df['phone'][1], '159****4321')
        
        # Check Other columns untouched
        self.assertEqual(masked_df['name'][0], 'Alice')

    def test_security_check(self):
        # Safe query
        self.assertTrue(self.vanna._is_read_only("SELECT * FROM users"))
        self.assertTrue(self.vanna._is_read_only("select count(*) from logs"))
        
        # Unsafe query
        self.assertFalse(self.vanna._is_read_only("DROP TABLE users"))
        self.assertFalse(self.vanna._is_read_only("DELETE FROM users WHERE id=1"))
        self.assertFalse(self.vanna._is_read_only("UPDATE users SET name='Hack'"))

if __name__ == '__main__':
    unittest.main()
