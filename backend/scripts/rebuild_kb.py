
import asyncio
import os
import sys
import logging
import nest_asyncio
nest_asyncio.apply()

# Add backend directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.append(backend_dir)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.db.session import AsyncSessionLocal
from app.services.lightrag_service import lightrag_service

async def run():
    # Get filenames from command line arguments
    args = sys.argv[1:]
    
    include_files = None
    if not args:
        logger.info("No arguments provided, using default hardcoded file.")
        include_files = ["每日新闻_工业互联网_2026.01.31.docx"]
    elif "--all" in args:
        logger.info("Targeting ALL files in the database.")
        include_files = None
    else:
        logger.info(f"Targeting files from CLI args: {args}")
        include_files = args

    logger.info("Starting knowledge base rebuild (chunking + vectorization)...")
    try:
        async with AsyncSessionLocal() as db:
            await lightrag_service.rebuild_store(
                db, 
                include_filenames=include_files,
                clear_existing=False
            )
        logger.info("Rebuild completed successfully.")
    except Exception as e:
        logger.error(f"Rebuild failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run())
