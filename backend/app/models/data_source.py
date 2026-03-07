from sqlalchemy import Column, DateTime, Integer, String, Text, JSON
from sqlalchemy.sql import func

from app.db.base import Base


class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    type = Column(String, nullable=False)  # mysql, postgresql, sftp, api, crawler
    host = Column(String, nullable=True) # made nullable for API/Crawler if URL is used
    port = Column(Integer, nullable=True) # made nullable
    username = Column(String, nullable=True)
    password_encrypted = Column(String, nullable=True)
    database = Column(String, nullable=True) # made nullable

    # Optional connection arguments (JSON string if needed, or simple fields)
    db_schema = Column("schema", String, nullable=True)  # For Postgres
    
    # New fields for other strategies
    url = Column(String, nullable=True)
    encrypted_api_key = Column(String, nullable=True)
    encrypted_private_key = Column(String, nullable=True)
    encrypted_token = Column(String, nullable=True)
    config = Column(JSON, nullable=True) # Generic config for flexibility

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    last_synced_at = Column(DateTime(timezone=True), nullable=True)

    description = Column(Text, nullable=True)
