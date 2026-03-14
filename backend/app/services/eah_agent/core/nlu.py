import json
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from agno.models.openai import OpenAIChat
from app.services.llm.factory import ModelFactory
from app.models.llm_model import LLMModel
from sqlalchemy.orm import Session # Import Session if needed for real usage, but here just mock/use model

class IntentResult(BaseModel):
    intent: str = Field(..., description="The intent of the user input. Either 'chat', 'task', 'data_query', or 'kg_qa'.")
    confidence: float = Field(..., description="The confidence score of the classification (0.0 to 1.0).")
    task_params: Optional[Dict[str, Any]] = Field(None, description="Extracted parameters if intent is 'task' or 'data_query'.")

class NluService:
    def __init__(self, llm_model: Optional[LLMModel] = None):
        if not llm_model:
            # Create a dummy model configuration for demo/default
            llm_model = LLMModel(
                model_id="gpt-3.5-turbo", 
                provider="openai", 
                api_key="dummy" # Should be replaced with real config in production
            )
        
        # Use ModelFactory which handles provider specifics
        try:
             self.model = ModelFactory.create_model(llm_model)
        except Exception as e:
             # Fallback if ModelFactory fails (e.g., requires real key)
             print(f"Warning: ModelFactory failed: {e}. Using dummy.")
             self.model = OpenAIChat(id="gpt-3.5-turbo", api_key="dummy")

    async def analyze(self, user_input: str) -> IntentResult:
        """
        Analyzes the user input to determine intent and extract parameters.
        """
        system_prompt = """
        You are an NLU (Natural Language Understanding) module for an agent system.
        Your task is to classify the user's input into one of six categories: 'chat', 'task', 'data_query', 'kg_qa', 'team', or 'workflow'.
        
        1. 'chat': General conversation, greetings, questions about the agent itself, or chit-chat.
        2. 'task': Specific requests to perform an action on the Openclaw platform (e.g., execute a crawler, monitor a site, check status).
        3. 'data_query': Natural language questions that require SQL queries on structured databases (e.g., "Show me sales > 1000", "Count users by city"). Key indicators: aggregations, specific metrics, table-like data requests.
        4. 'kg_qa': Questions about relationships, entities, or unstructured knowledge graph queries (e.g., "What is the relationship between X and Y?", "Who founded company Z?").
        5. 'team': Requests that explicitly mention a team, collaboration, or require multiple specialized agents (e.g., "Assemble a research team", "Have the operations team check this").
        6. 'workflow': Requests that imply a multi-step defined process or standard operating procedure (e.g., "Start the report generation workflow", "Run the daily data pipeline").

        If the intent is 'task', you must also extract the following structured parameters:
        - task_type: The type of task (e.g., 'crawler', 'monitor', 'health_check'). Infer from context.
        - target: The target URL or identifier (e.g., 'https://example.com').
        - timeout: (Optional) Timeout in seconds. Default to 60 if not specified.
        - retry_policy: (Optional) A dictionary with 'max_attempts' and 'backoff_factor'. Default to {max_attempts: 3, backoff_factor: 1.0}.

        If the intent is 'team', extract:
        - team_type: The type of team needed (e.g., 'research', 'operations', 'dynamic'). Default to 'dynamic' if unsure.
        - roles: A list of specific roles mentioned (e.g., ['writer', 'reviewer']).
        - goal: The high-level goal for the team.

        If the intent is 'workflow', extract:
        - workflow_name: The name of the workflow (e.g., 'report_generation', 'data_pipeline').
        - steps: (Optional) A list of high-level steps if explicitly mentioned.

        If the intent is 'data_query', check if confidence is high (>= 0.85). If not sure, default to 'kg_qa'.

        Output format: JSON only.
        Example JSON:
        {
            "intent": "data_query",
            "confidence": 0.95,
            "task_params": {}
        }
        """

        try:
            response = self.model.response(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                response_format={"type": "json_object"} # Ensure JSON output if supported, or rely on prompt
            )
            
            content = response.content
            # Clean up potential markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
                
            data = json.loads(content)
            return IntentResult(**data)
            
        except Exception as e:
            # Fallback for errors or low confidence
            return IntentResult(intent="chat", confidence=0.0)

