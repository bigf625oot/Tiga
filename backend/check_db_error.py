import asyncio
from app.db.session import AsyncSessionLocal
from app.models.knowledge import KnowledgeDocument
from sqlalchemy import select

async def check_error():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(KnowledgeDocument).order_by(KnowledgeDocument.created_at.desc()))
        docs = result.scalars().all()
        for doc in docs:
            print(f"ID: {doc.id}, File: {doc.filename}, Status: {doc.status}")
            if doc.error_message:
                print(f"Error: {doc.error_message}")
            print("-" * 30)

if __name__ == "__main__":
    asyncio.run(check_error())