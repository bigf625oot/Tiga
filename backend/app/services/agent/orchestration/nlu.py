import logging
import asyncio
from typing import Optional, Any, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.llm_model import LLMModel
from app.services.agent.schemas.intent import IntentResult
from app.services.platform.llm.factory import ModelFactory
from app.services.agent.tools.retriever import tool_retriever
from agno.agent import Agent

logger = logging.getLogger("eah.core.nlu")

class NluService:
    """
    Agent NLU Service: Translates natural language into agent intents,
    taking into account user input, current mode hint, and conversation history.
    Now implements Dual-Track Retrieval (Intent + Tools RAG).
    """
    def __init__(self, llm_model: Optional[LLMModel] = None):
        self.llm_model = llm_model

    async def analyze(
        self, 
        user_input: str, 
        mode_hint: Optional[str] = None, 
        session_id: Optional[str] = None, 
        db: Optional[AsyncSession] = None
    ) -> IntentResult:
        """
        Analyzes user input and returns an IntentResult with suggested tools.
        Supported intents for Agent: "chat", "task", "team", "workflow", "data_query", "kg_qa"
        """
        # 1. 宏观意图推断 (Macro Intent)
        base_intent = await self._analyze_intent(user_input, mode_hint, session_id, db)
        
        # 2. 微观工具召回 (Micro Tools RAG)
        # 只有非纯聊天的场景才需要去召回工具，或者当识别为 lite 但有特定关键词时
        suggested_tools = []
        if base_intent.intent != "chat" or mode_hint == "quick":
            # 根据用户的具体 Query 和宏观范式，动态召回最相关的 Top-K 工具
            suggested_tools = await tool_retriever.retrieve(
                query=user_input, 
                top_k=3, 
                paradigm=base_intent.paradigm
            )
            base_intent.suggested_tools = suggested_tools
            
        return base_intent

    async def _analyze_intent(
        self, 
        user_input: str, 
        mode_hint: Optional[str] = None, 
        session_id: Optional[str] = None, 
        db: Optional[AsyncSession] = None
    ) -> IntentResult:
        """
        Analyzes user input and returns an IntentResult.
        Supported intents for Agent: "chat", "task", "team", "workflow", "data_query", "kg_qa"
        """
        try:
            history_context = ""
            if db and session_id:
                try:
                    from app.services.agent.components import DefaultMemoryManager
                    mm = DefaultMemoryManager(db=db)
                    hist = await mm.get_history(session_id, limit=6)
                    if hist:
                        history_lines = []
                        for msg in hist:
                            role = msg.get("role", "unknown") if isinstance(msg, dict) else getattr(msg, "role", "unknown")
                            content = msg.get("content", "") if isinstance(msg, dict) else getattr(msg, "content", "")
                            if role and content:
                                history_lines.append(f"{role}: {content[:200]}")
                        if history_lines:
                            history_context = "Recent Conversation History:\n" + "\n".join(history_lines)
                except Exception as e:
                    logger.warning(f"Failed to fetch history for NLU: {e}")

            # If we don't have a model, fallback to heuristics
            if not self.llm_model:
                return self._fallback_heuristic(user_input, mode_hint)

            # Create an Agno Agent for intent classification
            model_instance = ModelFactory.create_model(self.llm_model)
            
            instructions = f"""You are an expert Intent Classifier for an AI assistant.
Your task is to classify the user's latest message into one of the following exact intent categories:

- "chat": General conversation, greetings, simple Q&A, explanations, summarizing text. No complex multi-step execution needed.
- "task": The user wants to execute a complex task, write code, build a project, create a plan, or execute step-by-step actions.
- "team": The user explicitly wants a team of multiple specialized agents to collaborate.
- "workflow": The user explicitly wants to run a predefined DAG or workflow.
- "data_query": The user is asking to query a database, write SQL, or look up structured data.
- "kg_qa": The user is asking about knowledge graph relationships or trends.

Current Mode Hint: {mode_hint or "None (Auto Mode)"}
(If a hint is provided, lean towards it unless the user's latest message clearly breaks away from it, e.g., asking a simple question during a task should be "chat".)

Output ONLY a valid JSON object with the following schema:
{{
    "intent": "<one of the categories>",
    "confidence": <float between 0.0 and 1.0>,
    "reasoning": "<brief explanation of why>"
}}
"""

            prompt = f"{history_context}\n\nUser's Latest Message: {user_input}\n\nOutput JSON:"

            agent = Agent(
                model=model_instance,
                instructions=instructions,
                markdown=False,
            )
            
            response = await agent.arun(prompt)
            content = getattr(response, "content", "").strip()
            
            # Parse JSON
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            import json
            data = json.loads(content)
            
            intent = data.get("intent", mode_hint or "chat")
            valid_intents = ["chat", "task", "team", "workflow", "data_query", "kg_qa"]
            if intent not in valid_intents:
                intent = mode_hint or "chat"
                
            return IntentResult(
                intent=intent,
                paradigm=IntentResult.resolve_paradigm(intent),
                confidence=float(data.get("confidence", 0.8)),
                reasoning=data.get("reasoning", "LLM classified"),
                parameters={}
            )

        except Exception as e:
            logger.warning(f"NLU LLM analysis failed: {e}. Falling back to heuristic.")
            return self._fallback_heuristic(user_input, mode_hint)

    def _fallback_heuristic(self, user_input: str, mode_hint: Optional[str]) -> IntentResult:
        lower_input = user_input.lower()
        agent_intent = mode_hint or "chat"
        
        if any(w in lower_input for w in ["任务", "执行", "计划", "task", "plan", "execute", "写一个", "帮我", "代码"]):
            agent_intent = "task"
        elif any(w in lower_input for w in ["团队", "协作", "team", "collaborate"]):
            agent_intent = "team"
        elif any(w in lower_input for w in ["工作流", "流程", "workflow", "flow"]):
            agent_intent = "workflow"
            
        return IntentResult(
            intent=agent_intent,
            paradigm=IntentResult.resolve_paradigm(agent_intent),
            confidence=0.5,
            reasoning="Fallback heuristic mapping",
            parameters={}
        )
