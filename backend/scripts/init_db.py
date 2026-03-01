
import asyncio
import sys
import os

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.base import Base
from app.db.session import engine
# Import models to ensure they are registered
from app.models import (
    agent,
    chat,
    data_source,
    graph_export,
    indicator,
    knowledge,
    llm_model,
    mcp,
    node,
    recording,
    service_category,
    skill,
    tool,
    user,
    user_script,
    user_tool,
    workflow,
)

async def init_db():
    print("Creating database tables...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database tables created successfully.")
    except Exception as e:
        print(f"Error creating database tables: {e}")

if __name__ == "__main__":
    # Fix for Windows loop policy
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(init_db())
