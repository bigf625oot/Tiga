import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.skill import Skill

logger = logging.getLogger(__name__)


class ContextLoader:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def load_context(self, db: Session, skills_config: Optional[Dict[str, Any]], task: str = None) -> str:
        """
        Dynamically loads context (instructions) based on selected skills.

        Args:
            db: Database session
            skills_config: The 'skills_config' JSON from Agent model
            task: The current task (optional, for future dynamic filtering)

        Returns:
            str: A combined string of instructions from selected skills.
        """
        if not skills_config:
            return ""

        context_parts = []

        # 1. Handle explicit skill selection (from Skill Library)
        selected_skill_ids = skills_config.get("selected_skills", [])
        if selected_skill_ids:
            try:
                # Assuming 'db' is an AsyncSession based on AgentManager usage
                # If it's sync, we use db.execute directly.
                # AgentManager passes AsyncSession.

                stmt = select(Skill).where(Skill.id.in_(selected_skill_ids)).where(Skill.is_active == True)
                result = await db.execute(stmt)
                skills = result.scalars().all()

                for skill in skills:
                    if skill.content:
                        part = f"### Skill: {skill.name}\n{skill.content}"
                        context_parts.append(part)

            except Exception as e:
                logger.error(f"Error loading skills context: {e}")

        # 2. Handle legacy or inline skills (if any)
        # ... (future expansion)

        if not context_parts:
            return ""

        return "\n\n".join(context_parts)


context_loader = ContextLoader.get_instance()
