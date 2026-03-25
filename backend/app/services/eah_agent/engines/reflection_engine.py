import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from agno.agent import Agent

from app.models.llm_model import LLMModel
from app.services.llm.factory import ModelFactory
from app.services.eah_agent.components.experience_store import DefaultExperienceStore

logger = logging.getLogger("eah.core.engines.reflection")

class ReflectionEngine:
    """
    Reflection Engine
    """
    def __init__(self, db: AsyncSession, experience_store: DefaultExperienceStore, llm_model: Optional[LLMModel] = None):
        self.db = db
        self.experience_store = experience_store
        self.llm_model = llm_model

    async def reflect_and_store(self, session_id: str, task_desc: str, execution_log: str, is_success: bool) -> str:
        """
        根据执行日志进行反思，并将经验入库。
        """
        if not self.llm_model:
            from app.services.llm.resolver import resolve_chat_llm_model
            self.llm_model = await resolve_chat_llm_model(self.db)
            
        model_instance = ModelFactory.create_model(self.llm_model)

        reflector = Agent(
            name="Reflector",
            model=model_instance,
            instructions=[
                "You are an expert system optimizing future agent performance.",
                "Extract concise, reusable rules or lessons from the execution log.",
                "If it was a success, note the successful approach.",
                "If it failed, identify the root cause and how to avoid it next time.",
                "Output ONLY a 1-3 sentence summary."
            ]
        )

        prompt = (
            f"Task: {task_desc}\n"
            f"Success: {is_success}\n"
            f"Execution Log:\n{execution_log}\n\n"
            "Provide your reflection summary."
        )

        try:
            response = await reflector.arun(prompt)
            summary = response.content if hasattr(response, 'content') else str(response)
            summary = summary.strip()

            try:
                await self.experience_store.save_experience(
                    session_id=session_id,
                    task_desc=task_desc,
                    experience_summary=summary,
                    is_success=is_success,
                )
                logger.info("reflection_persisted session_id=%s", session_id)
            except Exception as e:
                logger.error("reflection_persist_failed session_id=%s err=%s", session_id, e)
            return summary
            
        except Exception as e:
            logger.error(f"Reflection failed: {e}")
            return ""
