from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, JSON
from datetime import datetime
from app.db.base import Base

class Indicator(Base):
    __tablename__ = "indicators"

    id = Column(Integer, primary_key=True, index=True)
    group = Column(String, index=True, nullable=False)
    name = Column(String, index=True, nullable=False)
    alias = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    advanced_options = Column(JSON, nullable=True) # Stores related_terms, formula, etc.
    is_deleted = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
