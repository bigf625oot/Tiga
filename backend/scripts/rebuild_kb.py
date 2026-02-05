
import asyncio
import os
import sys
import logging
import nest_asyncio
nest_asyncio.apply()

# Add current directory to path to find 'app'
sys.path.append(os.getcwd())

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.db.session import AsyncSessionLocal
from app.services.lightrag_service import lightrag_service

async def run():
    logger.info("Starting knowledge base rebuild (chunking + vectorization)...")
    try:
        async with AsyncSessionLocal() as db:
            await lightrag_service.rebuild_store(
                db, 
                include_filenames=["数势科技AI+DATA智能体及金融案例202509.pdf"],
                clear_existing=False
            )
        logger.info("Rebuild completed successfully.")
    except Exception as e:
        logger.error(f"Rebuild failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run())
