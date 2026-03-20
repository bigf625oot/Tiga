from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.db.session import get_db
from app.models.mcp import MCPServer
from app.models.skill import Skill
from app.models.user_market_item import UserMarketItem
from app.schemas.service_market import MarketInstalledResponse, MarketInstallRequest, MarketItemType


router = APIRouter()


async def _ensure_item_exists(db: AsyncSession, item_type: MarketItemType, item_id: str) -> None:
    if item_type == "skill":
        stmt = select(Skill.id).where(Skill.id == item_id, Skill.is_active.is_(True))
    else:
        stmt = select(MCPServer.id).where(MCPServer.id == item_id, MCPServer.is_active.is_(True))

    result = await db.execute(stmt)
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found or inactive")


@router.get("/installed", response_model=MarketInstalledResponse)
async def list_installed(
    user_id: str = Depends(deps.get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(UserMarketItem.item_type, UserMarketItem.item_id).where(UserMarketItem.user_id == user_id)
    result = await db.execute(stmt)
    rows = result.all()

    data = {"mcp": [], "skill": []}
    for item_type, item_id in rows:
        if item_type in data:
            data[item_type].append(item_id)

    return data


@router.post("/installed")
async def install_item(
    payload: MarketInstallRequest,
    user_id: str = Depends(deps.get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await _ensure_item_exists(db, payload.type, payload.id)

    try:
        db.add(UserMarketItem(user_id=user_id, item_type=payload.type, item_id=payload.id))
        await db.commit()
    except IntegrityError:
        await db.rollback()

    return {"ok": True}


@router.delete("/installed/{item_type}/{item_id}")
async def uninstall_item(
    item_type: MarketItemType,
    item_id: str,
    user_id: str = Depends(deps.get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(UserMarketItem).where(
        UserMarketItem.user_id == user_id,
        UserMarketItem.item_type == item_type,
        UserMarketItem.item_id == item_id,
    )
    result = await db.execute(stmt)
    row = result.scalars().first()
    if not row:
        return {"ok": True}

    await db.delete(row)
    await db.commit()
    return {"ok": True}

