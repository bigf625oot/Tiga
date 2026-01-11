import asyncio
import sys
import os

# Ensure current directory is in path
sys.path.append(os.getcwd())

from app.db.session import AsyncSessionLocal
from app.models.llm_model import LLMModel
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        print("Checking LLM Models...")
        try:
            res = await db.execute(select(LLMModel))
            models = res.scalars().all()
            for m in models:
                print(f"Model: {m.name}, ID: {m.model_id}, Type: {m.model_type}, Active: {m.is_active}")
        except Exception as e:
            print(f"Error checking models: {e}")

if __name__ == "__main__":
    asyncio.run(main())
