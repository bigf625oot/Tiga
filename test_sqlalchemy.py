import asyncio
from sqlalchemy import select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Boolean

Base = declarative_base()

class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"
    id = Column(Integer, primary_key=True)
    is_deleted = Column(Boolean, default=False)

stmt = select(KnowledgeDocument).where(not KnowledgeDocument.is_deleted)
print(stmt)
