from typing import Optional, List, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from agno.agent import Agent as AgnoAgent
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools
# from agno.tools.python import PythonTools # Assuming this exists or similar
from app.models.agent import Agent as AgentModel
from app.models.llm_model import LLMModel
from app.models.chat import ChatMessage
from app.services.knowledge_base import kb_service
import json
import logging

logger = logging.getLogger(__name__)

from app.services.model_factory import ModelFactory
from app.core.config import settings

def has_global_api_key():
    return bool(settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.startswith("sk-"))

class AgentManager:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def create_agno_agent(self, db: AsyncSession, agent_id: str, session_id: str = None) -> AgnoAgent:
        try:
            # 1. Fetch Agent Config
            result = await db.execute(select(AgentModel).filter(AgentModel.id == agent_id))
            agent_model = result.scalars().first()
            if not agent_model:
                raise ValueError(f"Agent {agent_id} not found")

            # 2. Fetch Model Config
            # Schema field is 'agent_model_config' but DB model uses 'model_config' (JSON)
            # SQLAlchemy model (AgentModel) uses 'model_config'.
            # Pydantic schema (AgentCreate/Response) uses 'agent_model_config'.
            # Here we are reading from DB model (SQLAlchemy), so it is 'model_config'.
            model_config = agent_model.model_config or {}
            llm_model_id = model_config.get("model_id")
            
            llm_model = None
            if llm_model_id:
                # Find the active model config from DB
                # First try to find active model with this model_id AND a non-empty API key
                res = await db.execute(
                    select(LLMModel)
                    .filter(LLMModel.model_id == llm_model_id, LLMModel.is_active == True, LLMModel.api_key != None, LLMModel.api_key != "")
                )
                llm_model = res.scalars().first()
                
                # If not found, fall back to just matching model_id (maybe user relies on env var, though unlikely for custom)
                if not llm_model:
                    res = await db.execute(select(LLMModel).filter(LLMModel.model_id == llm_model_id, LLMModel.is_active == True))
                    llm_model = res.scalars().first()
            
            # Fallback to default if not found or if found model has no key and global key is missing
            # We check if the found model has a valid key. If not, and we are here, it means we might crash.
            # So we try to find ANY model with a valid key.
            
            should_fallback = False
            if not llm_model:
                should_fallback = True
            # IMPORTANT: Check if llm_model has api_key. If not, check global key.
            # If both are missing, we MUST fallback.
            elif not llm_model.api_key and not has_global_api_key(): 
                should_fallback = True
                
            if should_fallback:
                # Try to find ANY active model with a valid key
                res = await db.execute(
                    select(LLMModel)
                    .filter(LLMModel.is_active == True, LLMModel.api_key != None, LLMModel.api_key != "")
                    .order_by(LLMModel.updated_at.desc())
                )
                fallback_model = res.scalars().first()
                if fallback_model:
                    if llm_model:
                        logger.warning(f"Agent requested model {llm_model.model_id} which has no key. Falling back to {fallback_model.model_id}.")
                    llm_model = fallback_model
                else:
                    # If still no model, maybe use the one without key and hope for the best (will likely fail with dummy)
                    if not llm_model:
                         # Re-fetch any active model even without key
                         res = await db.execute(select(LLMModel).filter(LLMModel.is_active == True).order_by(LLMModel.updated_at.desc()))
                         llm_model = res.scalars().first()

            if not llm_model:
                raise ValueError("No active LLM model found")

            # 3. Configure LLM using Factory
            model = ModelFactory.create_model(llm_model)

            # 4. Configure Tools
            tools = []
            tools_config = agent_model.tools_config or []
            skills_config = agent_model.skills_config or {}
            
            # Standard Tools
            if "duckduckgo" in tools_config or (skills_config.get("browser", {}).get("enabled")):
                tools.append(DuckDuckGoTools())
                
            # N8N Tools
            if "n8n" in tools_config:
                from app.tools.n8n import N8NTools
                from app.models.workflow import Workflow
                # Fetch active workflows
                wf_res = await db.execute(select(Workflow).filter(Workflow.is_active == True))
                workflows = wf_res.scalars().all()
                if workflows:
                    # Convert to dicts
                    wf_dicts = [{"name": w.name, "webhook_url": w.webhook_url} for w in workflows]
                    tools.append(N8NTools(workflows=wf_dicts))

            # Python Tools (Mock or Real)
            if skills_config.get("python", {}).get("enabled"):
                # from agno.tools.python import PythonTools
                # tools.append(PythonTools())
                pass # Skipping for now as environment might lack dependencies

            # Knowledge Base
            knowledge = None
            # Only enable knowledge if documents are selected OR if using global knowledge
            # But `kb_service.knowledge` might be None if no OpenAI key, which causes crash if we try to use it
            # And if `search_knowledge` is True but `knowledge` is None, Agno might complain
            
            has_documents = agent_model.knowledge_config and agent_model.knowledge_config.get("document_ids")
            if has_documents:
                 # Check if kb_service is initialized properly
                 if kb_service.knowledge:
                     knowledge = kb_service.knowledge
                 else:
                     # If global KB is not available (e.g. no embedding model), we should probably warn or skip
                     logger.warning(f"Agent {agent_model.name} requests knowledge but KB service is not ready.")
                     # IMPORTANT: Do not set knowledge if it's not ready, otherwise Agent creation might fail or behave unexpectedly
                     knowledge = None 
            
            # NOTE: Agno Agent will crash if `search_knowledge=True` but `knowledge=None`.
            # So we must ensure search_knowledge is only True if knowledge is valid.
            search_knowledge = bool(knowledge)

            # 5. Load History
            history = []
            if session_id:
                # Load recent messages (e.g. last 20)
                msgs = await db.execute(
                    select(ChatMessage)
                    .filter(ChatMessage.session_id == session_id)
                    .order_by(ChatMessage.created_at.asc())
                )
                chat_logs = msgs.scalars().all()
                pass

            # 6. Create Agent
            is_reasoning = ModelFactory.should_use_agno_reasoning(llm_model)
            is_native_reasoning = ModelFactory.is_reasoning_model(llm_model)

            # Instructions handling:
            # If user provides system_prompt, use it.
            # Otherwise default to "You are a helpful assistant."
            instructions = agent_model.system_prompt
            if not instructions:
                instructions = "You are a helpful assistant."
                
            # Agno Agent `instructions` parameter can be a string or list of strings.
            # It is usually used as the SYSTEM PROMPT.
            # However, `description` is also used.
            # Let's ensure system_prompt is passed correctly.

            agent = AgnoAgent(
                name=agent_model.name,
                model=model,
                description=agent_model.description, # Pass description
                instructions=instructions,
                tools=tools,
                knowledge=knowledge,
                search_knowledge=search_knowledge,
                markdown=True,
                reasoning=is_reasoning, 
                # show_reasoning=True, # Removed as it causes TypeError in current Agno version
            )
            
            return agent
        except Exception as e:
            logger.exception(f"Error creating agent {agent_id}")
            raise e

agent_manager = AgentManager.get_instance()
