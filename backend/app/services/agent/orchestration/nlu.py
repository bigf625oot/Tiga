import logging
import asyncio
from typing import Optional, Any, Dict
from app.models.llm_model import LLMModel
from app.services.agent.schemas.intent import IntentResult
from app.services.intelligence.nlu.classifier import IntentClassifier, QueryIntent

logger = logging.getLogger("eah.core.nlu")

class NluService:
    """
    Agent NLU Service: Translates natural language into agent intents.
    Returns IntentResult which the ModeRouter uses to route requests.
    """
    def __init__(self, llm_model: Optional[LLMModel] = None):
        self.llm_model = llm_model

    async def analyze(self, user_input: str) -> IntentResult:
        """
        Analyzes user input and returns an IntentResult.
        Default intents for Agent: "chat", "task", "team", "workflow", "data_query", "kg_qa"
        """
        try:
            classifier = IntentClassifier.get_instance()
            result = await classifier.classify_detailed(user_input)
            
            # Map QueryIntent to Agent Intent
            intent_map = {
                QueryIntent.SQL_QUERY: "data_query",
                QueryIntent.STRUCTURED_QUERY: "data_query",
                QueryIntent.KG_QUERY: "kg_qa",
                QueryIntent.RAG_QUERY: "chat",
                QueryIntent.UNKNOWN: "chat"
            }
            
            # Additional heuristic for Agent intents
            lower_input = user_input.lower()
            agent_intent = "chat"
            
            if any(w in lower_input for w in ["任务", "执行", "计划", "task", "plan", "execute"]):
                agent_intent = "task"
            elif any(w in lower_input for w in ["团队", "协作", "team", "collaborate"]):
                agent_intent = "team"
            elif any(w in lower_input for w in ["工作流", "流程", "workflow", "flow"]):
                agent_intent = "workflow"
            else:
                agent_intent = intent_map.get(result.intent, "chat")
                
            parameters = {}
            if result.parameters:
                parameters = result.parameters.model_dump(exclude_none=True)

            return IntentResult(
                intent=agent_intent,
                confidence=result.confidence,
                reasoning=result.reasoning or "Heuristic mapped",
                parameters=parameters
            )
        except Exception as e:
            logger.warning(f"NLU analysis failed: {e}. Falling back to 'chat'.")
            return IntentResult(
                intent="chat",
                confidence=0.0,
                reasoning=str(e),
                parameters={}
            )
