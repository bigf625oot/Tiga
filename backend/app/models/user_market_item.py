import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.sql import func

from app.db.base import Base


class UserMarketItem(Base):
    __tablename__ = "user_market_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    item_type = Column(String, nullable=False)
    item_id = Column(String, nullable=False)
    installed_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "item_type", "item_id", name="uix_user_market_items"),
        Index("ix_user_market_items_user_type_id", "user_id", "item_type", "item_id"),
    )

