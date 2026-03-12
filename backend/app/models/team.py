from typing import List, Optional
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Text
from app.db.base import Base

class Team(Base):
    __tablename__ = "team"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    mode = Column(String, nullable=False, default="coordinate")  # coordinate, route, broadcast, tasks
    leader_id = Column(String, nullable=True) # The ID of the agent acting as leader
    icon = Column(String, nullable=True)
    members = Column(JSON, nullable=False, default=[])  # List of member agent IDs
    is_readonly = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
