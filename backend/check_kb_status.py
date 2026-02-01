
import asyncio
import os
import sys

# Add current directory to path to find 'app'
sys.path.append(os.getcwd())

from app.db.session import AsyncSessionLocal
from sqlalchemy import select
from app.models.knowledge import KnowledgeDocument

async def run():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(KnowledgeDocument).order_by(KnowledgeDocument.created_at.desc()))
        docs = res.scalars().all()
        print("\nID | Filename | Status | Progress/Error")
        print("-" * 80)
        for d in docs:
            print(f"{d.id} | {d.filename} | {d.status} | {d.error_message}")

if __name__ == "__main__":
    asyncio.run(run())
