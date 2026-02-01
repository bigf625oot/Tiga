import asyncio
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.llm_model import LLMModel

async def check_models():
    async with AsyncSessionLocal() as db:
        res = await db.execute(
            select(LLMModel)
            .filter(LLMModel.is_active == True, LLMModel.model_type == "embedding")
        )
        model = res.scalars().first()
        if model:
            print(f"Active Embedding Model: {model.name}")
            print(f"Model ID: {model.model_id}")
            print(f"Base URL: {model.base_url}")
            print(f"Provider: {model.provider}")
        else:
            print("No active embedding model found.")

if __name__ == "__main__":
    asyncio.run(check_models())
