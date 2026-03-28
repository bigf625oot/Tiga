from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.models.skill import Skill as SkillModel
from app.services.agent.skills.skill import Skill

class DatabaseLoader:
    """Loader for fetching skills from the database."""
    
    def __init__(self, db: AsyncSession, allowed_ids: Optional[List[str]] = None, allowed_names: Optional[List[str]] = None):
        self.db = db
        self.allowed_ids = allowed_ids or []
        self.allowed_names = allowed_names or []
        
    async def aload(self) -> List[Skill]:
        """Async load skills from the database."""
        if not self.allowed_ids and not self.allowed_names:
            return []
            
        conds = []
        if self.allowed_ids: conds.append(SkillModel.id.in_(self.allowed_ids))
        if self.allowed_names: conds.append(SkillModel.name.in_(self.allowed_names))
        
        stmt = select(SkillModel).where(SkillModel.is_active.is_(True), or_(*conds))
        res = await self.db.execute(stmt)
        
        skills = []
        for r in res.scalars().all():
            skills.append(Skill(
                name=r.name,
                description=r.description or "",
                instructions=r.content or "",
                source_path=f"db:{r.id}",
                metadata=r.meta_data or None,
            ))
        return skills
