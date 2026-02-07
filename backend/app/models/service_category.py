import uuid
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.sql import func
from app.db.base import Base

class ServiceCategory(Base):
    __tablename__ = "service_categories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    slug = Column(String, unique=True, index=True, nullable=False)  # e.g., "productivity", "analysis"
    label = Column(String, nullable=False)  # e.g., "办公效率"
    icon = Column(String, nullable=True)  # e.g., "⚡"
    sort_order = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
