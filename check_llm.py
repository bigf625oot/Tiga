
import asyncio
import os
import sys
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# 添加 backend 路径到 sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.core.config import settings
from app.models.llm_model import LLMModel

async def check_llm_config():
    # 尝试在 backend 目录下查找 taichi.db
    db_path = "./backend/taichi.db"
    if not os.path.exists(db_path):
        # 尝试直接在当前目录查找 (如果 CWD 是 backend)
        if os.path.exists("taichi.db"):
            db_path = "taichi.db"
        else:
             # 尝试上一级
             if os.path.exists("../taichi.db"):
                 db_path = "../taichi.db"
             else:
                 print("Database file not found in ./backend/taichi.db or ./taichi.db")
                 # 列出 backend 目录看看
                 print(f"Listing backend dir: {os.listdir('./backend')}")
                 return

    db_url = f"sqlite+aiosqlite:///{db_path}"
    print(f"Connecting to {db_url}")

    engine = create_async_engine(db_url)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as session:
        print("Checking Active LLM Models...")
        stmt = select(LLMModel).filter(LLMModel.is_active == True)
        result = await session.execute(stmt)
        models = result.scalars().all()
        
        if not models:
            print("No active LLM models found!")
        else:
            for m in models:
                print(f"Model: {m.name}, Type: {m.model_type}, Provider: {m.provider}, BaseURL: {m.base_url}")

if __name__ == "__main__":
    asyncio.run(check_llm_config())
