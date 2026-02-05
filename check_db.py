
import asyncio
import sys
from pathlib import Path

# Add backend to sys.path
backend_path = Path(__file__).resolve().parent / "backend"
sys.path.append(str(backend_path))

from app.db.session import AsyncSessionLocal
from app.models.llm_model import LLMModel
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        print("--- Active LLM Models (type != embedding) ---")
        res = await db.execute(
            select(LLMModel)
            .filter(LLMModel.is_active == True, LLMModel.model_type != "embedding")
        )
        llms = res.scalars().all()
        for m in llms:
            print(f"ID: {m.id}, Name: {m.name}, Type: {m.model_type}, Active: {m.is_active}")

        print("\n--- Active Embedding Models (type == embedding) ---")
        res = await db.execute(
            select(LLMModel)
            .filter(LLMModel.is_active == True, LLMModel.model_type == "embedding")
        )
        embeds = res.scalars().all()
        for m in embeds:
            print(f"ID: {m.id}, Name: {m.name}, Type: {m.model_type}, Active: {m.is_active}")

        print("\n--- All Models ---")
        res = await db.execute(select(LLMModel))
        all_models = res.scalars().all()
        for m in all_models:
            print(f"ID: {m.id}, Name: {m.name}, Type: {m.model_type}, Active: {m.is_active}")

if __name__ == "__main__":
    asyncio.run(main())
