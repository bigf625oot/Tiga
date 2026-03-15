from __future__ import annotations

from typing import Iterable, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.llm_model import LLMModel


def _normalize_types(prefer_types: Optional[Iterable[str]]) -> Optional[list[str]]:
    if not prefer_types:
        return None
    out: list[str] = []
    for t in prefer_types:
        if not t:
            continue
        s = str(t).strip().lower()
        if s and s not in out:
            out.append(s)
    return out or None


async def resolve_active_llm_model(
    db: AsyncSession,
    *,
    model_id: Optional[str] = None,
    prefer_types: Optional[Iterable[str]] = None,
    require_api_key: bool = True,
) -> Optional[LLMModel]:
    prefer_types_norm = _normalize_types(prefer_types)

    base_filters = [LLMModel.is_active == True]
    if model_id:
        base_filters.append(LLMModel.model_id == model_id)
    if prefer_types_norm:
        base_filters.append(LLMModel.model_type.in_(prefer_types_norm))

    if require_api_key:
        with_key_stmt = (
            select(LLMModel)
            .where(
                *base_filters,
                LLMModel.api_key != None,
                LLMModel.api_key != "",
            )
            .order_by(LLMModel.updated_at.desc())
        )
        res = await db.execute(with_key_stmt)
        m = res.scalars().first()
        if m:
            return m

    stmt = select(LLMModel).where(*base_filters).order_by(LLMModel.updated_at.desc())
    res = await db.execute(stmt)
    return res.scalars().first()


async def resolve_chat_llm_model(
    db: AsyncSession,
    *,
    model_id: Optional[str] = None,
    allow_multimodal: bool = True,
) -> Optional[LLMModel]:
    prefer_types = ["multimodal", "text"] if allow_multimodal else ["text"]
    m = await resolve_active_llm_model(
        db,
        model_id=model_id,
        prefer_types=prefer_types,
        require_api_key=True,
    )
    if m:
        return m
    return await resolve_active_llm_model(
        db,
        model_id=model_id,
        prefer_types=prefer_types,
        require_api_key=False,
    )

