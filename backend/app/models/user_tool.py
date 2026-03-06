import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.sql import func
from app.db.base import Base

class UserTool(Base):
    __tablename__ = "user_tool"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    tool_id = Column(String, ForeignKey("tools.id", ondelete="CASCADE"), nullable=False)
    granted_at = Column(DateTime(timezone=True), server_default=func.now())
    granted_by = Column(String, nullable=True)  # UUID of the user who granted access
    expires_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint('user_id', 'tool_id', name='uix_user_tool'),
        Index('ix_user_tool_user_id_tool_id', 'user_id', 'tool_id'),
    )
