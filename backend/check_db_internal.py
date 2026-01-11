import asyncio
import sys
import os

# Ensure current directory is in path
sys.path.append(os.getcwd())

from app.db.session import AsyncSessionLocal
from app.models.chat import ChatMessage, ChatSession
from app.models.agent import Agent
from app.models.knowledge import KnowledgeDocument
from app.models.llm_model import LLMModel
from app.models.recording import Recording
from app.models.workflow import Workflow
from sqlalchemy import select, desc

async def main():
    async with AsyncSessionLocal() as db:
        print("Checking Agents...")
        try:
            res = await db.execute(select(Agent))
            agents = res.scalars().all()
            for a in agents:
                print(f"Agent: {a.name}, ID: {a.id}")
                print(f"  Knowledge Config: {a.knowledge_config}")
        except Exception as e:
            print(f"Error checking agents: {e}")
        
        print("\nChecking Knowledge Documents...")
        try:
            res = await db.execute(select(KnowledgeDocument))
            docs = res.scalars().all()
            for d in docs:
                print(f"Doc: {d.filename}, ID: {d.id}, Status: {d.status}")
                print(f"  Error: {d.error_message}")
        except Exception as e:
            print(f"Error checking docs: {e}")

if __name__ == "__main__":
    asyncio.run(main())
