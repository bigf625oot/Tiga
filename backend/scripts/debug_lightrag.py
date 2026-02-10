
import asyncio
import os
import sys
from sqlalchemy import select

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import AsyncSessionLocal
from app.models.llm_model import LLMModel
from app.models.knowledge import KnowledgeDocument

async def check_status():
    async with AsyncSessionLocal() as db:
        print("--- Checking LLM Models ---")
        res = await db.execute(select(LLMModel))
        models = res.scalars().all()
        active_llm = None
        active_embed = None
        for m in models:
            print(f"Model: {m.model_id}, Type: {m.model_type}, Active: {m.is_active}, Provider: {m.provider}")
            if m.is_active:
                if m.model_type == "embedding":
                    active_embed = m
                else:
                    active_llm = m
        
        if not active_llm:
            print("[ERROR] No active LLM model found!")
        else:
            print(f"[OK] Active LLM: {active_llm.model_id}")

        if not active_embed:
            print("[ERROR] No active Embedding model found!")
        else:
            print(f"[OK] Active Embedding: {active_embed.model_id}")

        print("\n--- Checking Knowledge Documents ---")
        res = await db.execute(select(KnowledgeDocument))
        docs = res.scalars().all()
        if not docs:
            print("No documents found.")
        for d in docs:
            print(f"Doc ID: {d.id}, Filename: {d.filename}, Status: {d.status}")
            if d.error_message:
                print(f"  Error Message: {d.error_message}")

if __name__ == "__main__":
    asyncio.run(check_status())
