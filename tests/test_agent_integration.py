import json
import os
import unittest
from string import Template

class TestAgentIntegration(unittest.TestCase):
    
    def setUp(self):
        self.file_path = "agent_prompt.json"
        with open(self.file_path, "r") as f:
            self.data = json.load(f)

    def test_prompt_substitution(self):
        """Simulate the agent initialization process."""
        prompt_template = self.data["prompt"]
        variables = self.data["variables"]
        
        # Mock environment variables
        mock_env = {
            "project_name": "IntegrationTestProject",
            "version": "2.0.0-beta",
            "environment": "test",
            "trace_id": "trace-12345"
        }
        
        # Perform substitution
        final_prompt = prompt_template
        for var_key, var_config in variables.items():
            env_key = var_key.strip("${}")
            value = mock_env.get(env_key, var_config["default"])
            final_prompt = final_prompt.replace(var_key, value)
            
        # Verify substitution
        self.assertIn("IntegrationTestProject", final_prompt)
        self.assertIn("2.0.0-beta", final_prompt)
        self.assertIn("trace-12345", final_prompt)
        
        # Verify no unresolved variables remain
        self.assertNotIn("${project_name}", final_prompt)
        self.assertNotIn("${version}", final_prompt)

    def test_tool_loading(self):
        """Simulate tool loading."""
        tools = self.data["tools"]
        loaded_tools = {}
        
        for tool in tools:
            loaded_tools[tool["name"]] = tool
            
        self.assertIn("web_search", loaded_tools)
        self.assertIn("python_tools", loaded_tools)
        self.assertIn("sql_tools", loaded_tools)
        
        # Check specific tool details
        self.assertEqual(loaded_tools["web_search"]["parameters"]["properties"]["max_results"]["default"], 5)

if __name__ == "__main__":
    unittest.main()
