from agno.tools import Toolkit
from typing import List, Dict
import requests
import json
import logging

logger = logging.getLogger(__name__)

class N8NTools(Toolkit):
    def __init__(self, workflows: List[Dict]):
        super().__init__(name="n8n_tools")
        self.workflows = workflows
        # Dynamically update docstring to include available workflows
        available_names = ", ".join([w['name'] for w in workflows])
        self.trigger_workflow.__doc__ = f"""
        Triggers a registered N8N workflow by name.
        
        Available workflows you can call: {available_names}
        
        Args:
            workflow_name (str): The exact name of the workflow to trigger.
            payload (str): JSON string payload to send to the workflow webhook. e.g. '{{"key": "value"}}'
            
        Returns:
            str: The response from the workflow or error message.
        """
        self.register(self.trigger_workflow)

    def trigger_workflow(self, workflow_name: str, payload: str = "{}") -> str:
        # Implementation found in __init__ docstring
        wf = next((w for w in self.workflows if w['name'] == workflow_name), None)
        if not wf:
            available = ", ".join([w['name'] for w in self.workflows])
            return f"Error: Workflow '{workflow_name}' not found. Available: {available}"
        
        url = wf['webhook_url']
        try:
            # Parse payload if string
            if isinstance(payload, str):
                try:
                    data = json.loads(payload)
                except:
                    data = {"raw_content": payload}
            else:
                data = payload
                
            logger.info(f"Triggering N8N workflow: {workflow_name} at {url} with {data}")
            response = requests.post(url, json=data, timeout=30)
            return f"Workflow triggered. Status: {response.status_code}. Response: {response.text[:500]}"
        except Exception as e:
            logger.error(f"N8N trigger error: {e}")
            return f"Error triggering workflow: {str(e)}"
