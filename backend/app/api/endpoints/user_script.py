from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.db.session import get_db
from app.models.user_script import UserScript
from app.schemas.user_script import UserScriptCreate, UserScriptUpdate, UserScriptResponse

router = APIRouter()

@router.get("/user_scripts", response_model=List[UserScriptResponse])
async def list_user_scripts(agent_id: Optional[str] = Query(None), db: AsyncSession = Depends(get_db)):
    if agent_id:
        res = await db.execute(select(UserScript).filter(UserScript.agent_id == agent_id).order_by(UserScript.sort_order.asc(), UserScript.created_at.asc()))
    else:
        res = await db.execute(select(UserScript).order_by(UserScript.created_at.desc()))
    return res.scalars().all()

@router.post("/user_scripts", response_model=UserScriptResponse)
async def create_user_script(script_in: UserScriptCreate, db: AsyncSession = Depends(get_db)):
    obj = UserScript(
        agent_id=script_in.agent_id,
        title=script_in.title,
        content=script_in.content,
        sort_order=script_in.sort_order or 0
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj

@router.put("/user_scripts/{script_id}", response_model=UserScriptResponse)
async def update_user_script(script_id: int, script_in: UserScriptUpdate, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(UserScript).filter(UserScript.id == script_id))
    obj = res.scalars().first()
    if not obj:
        raise HTTPException(status_code=404, detail="UserScript not found")
    if script_in.title is not None:
        obj.title = script_in.title
    if script_in.content is not None:
        obj.content = script_in.content
    if script_in.sort_order is not None:
        obj.sort_order = script_in.sort_order
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj

@router.delete("/user_scripts/{script_id}")
async def delete_user_script(script_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(UserScript).filter(UserScript.id == script_id))
    obj = res.scalars().first()
    if not obj:
        raise HTTPException(status_code=404, detail="UserScript not found")
    await db.delete(obj)
    await db.commit()
    return {"status": "deleted"}
