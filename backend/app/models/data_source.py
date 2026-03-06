from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.db.base import Base


class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    type = Column(String, nullable=False)  # mysql, postgresql, etc.
    host = Column(String, nullable=False)
    port = Column(Integer, nullable=False)
    username = Column(String, nullable=True)
    password_encrypted = Column(String, nullable=True)
    database = Column(String, nullable=False)

    # Optional connection arguments (JSON string if needed, or simple fields)
    db_schema = Column("schema", String, nullable=True)  # For Postgres

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    last_synced_at = Column(DateTime(timezone=True), nullable=True)

    description = Column(Text, nullable=True)
