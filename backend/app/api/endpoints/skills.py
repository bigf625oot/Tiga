from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List, Optional
from app.db.session import get_db
from app.models.skill import Skill
from app.schemas.skill import SkillCreate, SkillUpdate, Skill as SkillSchema

router = APIRouter()

@router.post("/", response_model=SkillSchema)
def create_skill(skill: SkillCreate, db: Session = Depends(get_db)):
    db_skill = Skill(**skill.model_dump())
    db.add(db_skill)
    db.commit()
    db.refresh(db_skill)
    return db_skill

@router.get("/", response_model=List[SkillSchema])
def read_skills(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    skills = db.execute(select(Skill).offset(skip).limit(limit)).scalars().all()
    return skills

@router.get("/{skill_id}", response_model=SkillSchema)
def read_skill(skill_id: str, db: Session = Depends(get_db)):
    skill = db.execute(select(Skill).where(Skill.id == skill_id)).scalar_one_or_none()
    if skill is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill

@router.put("/{skill_id}", response_model=SkillSchema)
def update_skill(skill_id: str, skill_update: SkillUpdate, db: Session = Depends(get_db)):
    skill = db.execute(select(Skill).where(Skill.id == skill_id)).scalar_one_or_none()
    if skill is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    update_data = skill_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(skill, key, value)
    
    db.commit()
    db.refresh(skill)
    return skill

@router.delete("/{skill_id}")
def delete_skill(skill_id: str, db: Session = Depends(get_db)):
    skill = db.execute(select(Skill).where(Skill.id == skill_id)).scalar_one_or_none()
    if skill is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    db.delete(skill)
    db.commit()
    return {"ok": True}
