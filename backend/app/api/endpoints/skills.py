from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.skill import Skill
from app.schemas.skill import Skill as SkillSchema
from app.schemas.skill import SkillCreate, SkillUpdate

router = APIRouter()


@router.post("/", response_model=SkillSchema)
async def create_skill(skill: SkillCreate, db: AsyncSession = Depends(get_db)):
    db_skill = Skill(**skill.model_dump())
    db.add(db_skill)
    await db.commit()
    await db.refresh(db_skill)
    return db_skill


@router.get("/", response_model=List[SkillSchema])
async def read_skills(
    skip: int = 0, 
    limit: int = 100, 
    q: Optional[str] = Query(None, description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category slug"),
    filter: Optional[str] = Query("all", description="Filter type: all, hot, new, official"),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Skill)

    # Search
    if q:
        search_filter = or_(
            Skill.name.ilike(f"%{q}%"),
            Skill.description.ilike(f"%{q}%")
        )
        stmt = stmt.where(search_filter)
        
    # Category Filter
    if category and category != "all":
        stmt = stmt.where(Skill.category == category)
        
    # Other Filters
    if filter == "official":
        stmt = stmt.where(Skill.is_official == True)
    
    # Sorting
    if filter == "hot":
        stmt = stmt.order_by(desc(Skill.downloads))
    elif filter == "new":
        stmt = stmt.order_by(desc(Skill.created_at))
    else:
        # Default sort
        stmt = stmt.order_by(desc(Skill.created_at))

    stmt = stmt.offset(skip).limit(limit)

    result = await db.execute(stmt)
    skills = result.scalars().all()
    return skills


@router.get("/{skill_id}", response_model=SkillSchema)
async def read_skill(skill_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    if skill is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.put("/{skill_id}", response_model=SkillSchema)
async def update_skill(skill_id: str, skill_update: SkillUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    if skill is None:
        raise HTTPException(status_code=404, detail="Skill not found")

    update_data = skill_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(skill, key, value)

    await db.commit()
    await db.refresh(skill)
    return skill


@router.delete("/{skill_id}")
async def delete_skill(skill_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    if skill is None:
        raise HTTPException(status_code=404, detail="Skill not found")

    await db.delete(skill)
    await db.commit()
    return {"ok": True}
