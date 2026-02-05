import asyncio
import sys
import os

# Add backend path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.db.session import AsyncSessionLocal
from app.models.knowledge import KnowledgeChat
from sqlalchemy import select

async def test():
    async with AsyncSessionLocal() as db:
        try:
            print("Querying history for doc_id=10...")
            stmt = select(KnowledgeChat).filter(KnowledgeChat.doc_id == 10)
            result = await db.execute(stmt)
            history = result.scalars().all()
            print(f"Found {len(history)} records.")
        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
