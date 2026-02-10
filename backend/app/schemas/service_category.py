from typing import Optional
from pydantic import BaseModel

class ServiceCategoryBase(BaseModel):
    slug: str
    label: str
    icon: Optional[str] = None
    sort_order: int = 0

class ServiceCategoryCreate(ServiceCategoryBase):
    pass

class ServiceCategory(ServiceCategoryBase):
    id: str

    class Config:
        from_attributes = True
