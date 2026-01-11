from typing import Generator, Any
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from app.services.knowledge_base import kb_service
from app.core.config import settings
from app.services.tools.duckduckgo import DuckDuckGoTools

from app.services.model_factory import ModelFactory

class QAAgentService:
    _instance = None
    
    def __init__(self):
        # ... (initialization logic kept as is or simplified if needed) ...
        # For now, we keep the default init as it uses settings, not DB model directly
        # But _update_model should use the factory
        
        # Use Knowledge service availability to decide search_knowledge
        has_kb = kb_service.knowledge is not None
        
        self.agent = Agent(
            name="Smart QA Agent",
            model=OpenAIChat(id="gpt-4o", api_key=settings.OPENAI_API_KEY or "dummy"),
            knowledge=kb_service.knowledge if has_kb else None,
            search_knowledge=has_kb,
            markdown=True,
            add_history_to_context=True,
            description="You are a helpful assistant for the Recorder app. Answer questions based on the knowledge base.",
            instructions=[
                "Always search the knowledge base first." if has_kb else "Use your general knowledge to answer questions.",
                "If the answer is found in the knowledge base, cite the source." if has_kb else "",
                "If not found, use your general knowledge but mention that it's not in the knowledge base." if has_kb else "",
                "If you need to search the web, use the `duckduckgo_search` tool.",
                "If you need to plan a complex task, think step-by-step."
            ],
            tools=[DuckDuckGoTools()], 
            reasoning=True, 
        )
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _update_model(self, llm_model):
        """
        Update the agent's model based on the LLMModel configuration using the centralized factory.
        """
        if not llm_model:
            return

        # Check if we need to update (simple check based on model_id)
        current_model = self.agent.model
        new_base_url = llm_model.base_url
        
        # Normalize base_url check (factory logic duplication just for check, or assume update is cheap)
        # Let's just create the new model and swap it, it's cheap object creation.
        
        # Determine reasoning settings using Factory
        is_native_reasoning = ModelFactory.is_reasoning_model(llm_model)
        should_use_agno_reasoning = ModelFactory.should_use_agno_reasoning(llm_model)
        
        # Handle history for reasoning models (DeepSeek R1 workaround)
        if is_native_reasoning:
            self.agent.add_history_to_context = False
            if hasattr(self.agent, 'memory') and self.agent.memory:
                self.agent.memory.clear()
        else:
            self.agent.add_history_to_context = True

        # Create new model using Factory
        self.agent.model = ModelFactory.create_model(llm_model)
        
        # Update Agent Reasoning Settings
        self.agent.reasoning = should_use_agno_reasoning
        self.agent.show_reasoning = is_native_reasoning or should_use_agno_reasoning

    def chat_stream(self, message: str, llm_model=None) -> Generator[Any, None, None]:
        if llm_model:
            self._update_model(llm_model)
            
        return self.agent.run(message, stream=True)

qa_service = QAAgentService.get_instance()
