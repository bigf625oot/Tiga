from __future__ import annotations

from typing import Iterable, Optional

from sqlalchemy import select, case
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

    base_filters = [LLMModel.filter_active()]
    if model_id:
        base_filters.append(LLMModel.model_id == model_id)
    if prefer_types_norm:
        base_filters.append(LLMModel.model_type.in_(prefer_types_norm))

    stmt = select(LLMModel).where(*base_filters)
    
    if require_api_key:
        # Strictly require API key
        stmt = stmt.where(LLMModel.filter_has_api_key())
    else:
        # Prefer API key but not required
        stmt = stmt.order_by(
            case((LLMModel.filter_has_api_key(), 1), else_=0).desc()
        )
        
    stmt = stmt.order_by(
        LLMModel.priority.desc(),
        LLMModel.updated_at.desc()
    )
    
    res = await db.execute(stmt)
    return res.scalars().first()


async def resolve_chat_llm_model(
    db: AsyncSession,
    *,
    model_id: Optional[str] = None,
    allow_multimodal: bool = True,
) -> Optional[LLMModel]:
    """
    聊天模型解析器。
    默认返回最合适的活跃模型，优先带 API Key 的，其次是高优先级的。
    """
    prefer_types = ["multimodal", "text"] if allow_multimodal else ["text"]
    return await resolve_active_llm_model(
        db,
        model_id=model_id,
        prefer_types=prefer_types,
        require_api_key=False,
    )


async def resolve_fast_llm_model(
    db: AsyncSession,
) -> Optional[LLMModel]:
    """
    全局快慢型 LLM 模型解析器
    优先返回非 reasoning 模型，且带 api_key 的
    """
    # 查找非 reasoning 的活跃模型
    stmt = (
        select(LLMModel)
        .where(
            LLMModel.filter_active(),
            LLMModel.filter_fast_models()
        )
        .order_by(
            case((LLMModel.filter_has_api_key(), 1), else_=0).desc(),
            LLMModel.priority.desc(),
            LLMModel.updated_at.desc()
        )
    )
    res = await db.execute(stmt)
    m = res.scalars().first()
    
    # 如果实在找不到，只能回退到普通的聊天模型
    if not m:
        m = await resolve_chat_llm_model(db)
        
    return m

