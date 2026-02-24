import asyncio
import sys
import os
from sqlalchemy import select

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import AsyncSessionLocal
from app.models.llm_model import LLMModel

MODELS_DATA = [
    {
        "name": "GPT-4o",
        "provider": "openai",
        "model_id": "gpt-4o",
        "model_type": "text",
        "is_active": True,
    },
    {
        "name": "GPT-4o Mini",
        "provider": "openai",
        "model_id": "gpt-4o-mini",
        "model_type": "text",
        "is_active": False,
    },
    {
        "name": "Text Embedding 3 Small",
        "provider": "openai",
        "model_id": "text-embedding-3-small",
        "model_type": "embedding",
        "is_active": True,
    },
    {
        "name": "DeepSeek Chat",
        "provider": "deepseek",
        "model_id": "deepseek-chat",
        "model_type": "text",
        "base_url": "https://api.deepseek.com",
        "is_active": False,
    },
    {
        "name": "Qwen Max",
        "provider": "aliyun",
        "model_id": "qwen-max",
        "model_type": "text",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "is_active": False,
    }
]

async def seed():
    async with AsyncSessionLocal() as db:
        print("Seeding LLM Models...")
        for data in MODELS_DATA:
            # Check existence by model_id
            result = await db.execute(select(LLMModel).where(LLMModel.model_id == data["model_id"]))
            existing = result.scalars().first()
            
            if not existing:
                print(f"Adding Model: {data['name']}")
                model = LLMModel(
                    name=data["name"],
                    provider=data["provider"],
                    model_id=data["model_id"],
                    model_type=data.get("model_type", "text"),
                    base_url=data.get("base_url"),
                    is_active=data["is_active"]
                )
                db.add(model)
            else:
                print(f"Model {data['name']} already exists.")
        
        await db.commit()
        print("Done!")

if __name__ == "__main__":
    # Fix for Windows loop policy
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed())
