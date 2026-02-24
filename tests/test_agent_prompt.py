import json
import os
import unittest
import jsonschema

class TestAgentPrompt(unittest.TestCase):
    
    def setUp(self):
        self.file_path = "agent_prompt.json"
        with open(self.file_path, "r") as f:
            self.data = json.load(f)
            
    def test_json_structure(self):
        """Test the top-level keys."""
        expected_keys = ["prompt", "variables", "tools", "extensions", "test_cases", "metrics"]
        self.assertTrue(all(key in self.data for key in expected_keys))
        
    def test_variables(self):
        """Test variable substitution."""
        prompt = self.data["prompt"]
        variables = self.data["variables"]
        
        # Check if all variables are defined in the prompt
        for var_name, var_info in variables.items():
            self.assertIn(var_name, prompt, f"Variable {var_name} not found in prompt text")
            self.assertIn("default", var_info, f"Default value missing for {var_name}")
            
    def test_tools(self):
        """Test tool definitions."""
        tools = self.data["tools"]
        self.assertIsInstance(tools, list)
        for tool in tools:
            self.assertIn("name", tool)
            self.assertIn("description", tool)
            if "functions" in tool:
                for func in tool["functions"]:
                    self.assertIn("name", func)
                    self.assertIn("description", func)
                    self.assertIn("parameters", func)
            else:
                self.assertIn("parameters", tool)
            
    def test_extensions_schema(self):
        """Test extension schema validation."""
        schema = self.data["extensions"]["validation_schema"]
        
        # Valid extension example
        valid_extension = {
            "name": "new_tool",
            "description": "A new tool",
            "api_endpoint": "http://api.example.com/tool",
            "method": "POST",
            "parameters": {"param1": "value1"}
        }
        
        try:
            jsonschema.validate(instance=valid_extension, schema=schema)
        except jsonschema.ValidationError as e:
            self.fail(f"Valid extension failed schema validation: {e}")
            
        # Invalid extension example (missing required field)
        invalid_extension = {
            "name": "new_tool",
            "description": "A new tool"
        }
        
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(instance=invalid_extension, schema=schema)
            
    def test_metrics(self):
        """Test SLA metrics."""
        metrics = self.data["metrics"]
        self.assertLessEqual(metrics["sla"]["p99_latency_ms"], 500)
        self.assertGreaterEqual(metrics["sla"]["success_rate_percent"], 99.9)

    def test_knowledge_base_requirements(self):
        """Test new knowledge base requirements."""
        prompt = self.data["prompt"]
        
        # 1. Check for multi-source keywords
        required_sources = ["Sandbox logs", "Local File System", "Git Repositories", "API Documentation", "Cross-Session History"]
        for source in required_sources:
            self.assertIn(source, prompt, f"Missing knowledge source: {source}")

        # 2. Check for trigger keywords
        trigger_keywords = ["how to", "example", "explain", "reference", "history"]
        for keyword in trigger_keywords:
            self.assertIn(keyword, prompt, f"Missing trigger keyword: {keyword}")
            
        # 3. Check for confidence score rule
        self.assertIn("confidence score is ≥ 0.8", prompt, "Missing confidence score rule")
        
        # 4. Check for privacy rule
        self.assertIn("STRICTLY PROHIBITED to leak sandbox temporary file paths", prompt, "Missing privacy rule")

    def test_knowledge_base_tool_definition(self):
        """Test knowledge base tool structure."""
        tools = {t["name"]: t for t in self.data["tools"]}
        self.assertIn("knowledge_base_tools", tools)
        
        kb_tools = tools["knowledge_base_tools"]
        functions = {f["name"]: f for f in kb_tools["functions"]}
        
        # Check search_knowledge_base
        self.assertIn("search_knowledge_base", functions)
        params = functions["search_knowledge_base"]["parameters"]
        self.assertIn("sources", params)
        self.assertIn("min_confidence", params)
        
        # Check get_recent_history
        self.assertIn("get_recent_history", functions)

if __name__ == "__main__":
    unittest.main()
