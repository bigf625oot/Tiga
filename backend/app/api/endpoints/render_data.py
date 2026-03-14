"""
Render Data Endpoint
前端接口：
- HTTP GET `/render-data/` 接口作用：渲染数据
前端功能：
- 渲染数据用于前端展示
前端文件：
- `app/frontend/src/pages/RenderData.vue`
功能模块：
- 数据渲染管理
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.knowledge import KnowledgeDocument

router = APIRouter()


@router.get("/render-data")
async def render_data(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    sortBy: str = Query("created_at"),
    order: str = Query("desc"),
):
    offset = (page - 1) * size
    sort_col = getattr(KnowledgeDocument, sortBy if sortBy in ["created_at", "filename", "id"] else "created_at")
    sort_expr = desc(sort_col) if order.lower() == "desc" else sort_col
    total_res = await db.execute(select(KnowledgeDocument))
    total = len(total_res.scalars().all())
    res = await db.execute(select(KnowledgeDocument).order_by(sort_expr).offset(offset).limit(size))
    docs = res.scalars().all()
    items = []
    for d in docs:
        items.append(
            {
                "id": d.id,
                "title": d.filename,
                "createTime": d.created_at.isoformat() if d.created_at else None,
                "coverImage": d.oss_url,
                "summary": "",
                "tags": [],
            }
        )
    return {"page": page, "size": size, "total": total, "items": items}
