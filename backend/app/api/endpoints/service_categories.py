import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.db.session import get_db
from app.models.service_category import ServiceCategory
from app.schemas.service_category import ServiceCategory as ServiceCategorySchema

router = APIRouter()

@router.get("/", response_model=List[ServiceCategorySchema])
async def list_service_categories(
    db: AsyncSession = Depends(get_db)
):
    """
    List all Service Categories.
    Forced reset to 2 categories: MCP and Skills.
    """
    
    # Check if we have the correct structure (simple heuristic: count)
    result = await db.execute(select(ServiceCategory))
    categories = result.scalars().all()
    
    expected_slugs = {"mcp", "skills"}
    current_slugs = {c.slug for c in categories}
    
    # If the categories don't match exactly what we want (e.g. we have "all", "productivity" etc.), reset them.
    # User requested strictly 2 categories.
    if current_slugs != expected_slugs:
        # Clear all
        await db.execute(delete(ServiceCategory))
        
        # Insert only the requested two
        defaults = [
            {"slug": "mcp", "label": "MCP", "icon": "", "sort_order": 1},
            {"slug": "skills", "label": "技能", "icon": "", "sort_order": 2},
        ]
        
        for cat in defaults:
            new_cat = ServiceCategory(**cat)
            db.add(new_cat)
        
        await db.commit()
        
        # Re-fetch
        result = await db.execute(select(ServiceCategory).order_by(ServiceCategory.sort_order))
        categories = result.scalars().all()

    return categories
