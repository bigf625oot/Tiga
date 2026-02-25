import json
import logging
from typing import List, Optional
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from app.schemas.task import SubTaskCreate
from app.core.config import settings

logger = logging.getLogger(__name__)

class TaskSplitter:
    def __init__(self, model_id: str = "gpt-4o"):
        api_key = settings.OPENAI_API_KEY
        base_url = None
        
        # Simple fallback for model config if needed
        # In a real app, we might inject the model instance or factory
        
        self.agent = Agent(
            model=OpenAIChat(id=model_id, api_key=api_key, base_url=base_url),
            description="You are a Task Architect.",
            instructions="Break down the user's request into atomic, executable steps.",
            markdown=True
        )

    async def split(self, task_prompt: str) -> List[SubTaskCreate]:
        system_prompt = """
        Break down the user's request into atomic, executable steps.
        Return a JSON list of steps with dependencies.
        The output must be a valid JSON list of objects.
        Each object must have:
        - name: str (short description)
        - task_type: str (one of: CODE_GEN, DATA_RETRIEVAL, API_CALL)
        - execution_order: int
        - dependencies: List[str] (names of tasks it depends on. Use names from this list)
        - input_context: Dict (optional input parameters)

        Example:
        [
            {"name": "search_info", "task_type": "DATA_RETRIEVAL", "execution_order": 0, "dependencies": [], "input_context": {"query": "foo"}},
            {"name": "process_data", "task_type": "CODE_GEN", "execution_order": 1, "dependencies": ["search_info"], "input_context": {}}
        ]
        
        Return ONLY the JSON. No markdown formatting.
        """
        
        try:
            # agno.Agent.arun returns a RunResponse object or similar, which has .content
            response = await self.agent.arun(system_prompt + "\n\nUser Request: " + task_prompt)
            
            content = response.content
            # Cleanup
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
                
            data = json.loads(content.strip())
            sub_tasks = []
            for item in data:
                sub_tasks.append(SubTaskCreate(**item))
            return sub_tasks
        except Exception as e:
            logger.error(f"Failed to split task: {e}")
            raise ValueError(f"Failed to parse task split result: {e}")
