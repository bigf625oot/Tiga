
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
    logger.info("Starting FULL knowledge base rebuild...")
    
    # Manually clean up first to avoid file locking issues in rebuild_store
    import shutil
    from pathlib import Path
    
    # Assuming we are in backend dir or root, we need to find data/lightrag_store
    # The service uses: DATA_DIR = Path("data") -> relative to CWD
    # We are running from backend/ via "python3 scripts/..." so CWD is backend/
    
    data_dir = Path("data/lightrag_store")
    if data_dir.exists():
        # [Safety] Backup instead of delete
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path(f"data/backups/lightrag_store_backup_{timestamp}")
        backup_dir.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Backing up existing store to {backup_dir.absolute()}...")
        try:
            shutil.move(str(data_dir), str(backup_dir))
            logger.info("Backup completed successfully.")
        except Exception as e:
            logger.warning(f"Backup failed: {e}. Proceeding with caution...")
            # If backup fails, we might still want to clear it if it's a rebuild script
            # But let's ask user or just fail safely? 
            # Given the user request "avoid data being cleared", we should probably NOT delete if backup fails.
            # However, for a rebuild script, if we don't clear, rebuild might fail.
            # Let's try to remove ONLY if backup failed but we really need to proceed?
            # No, user said "avoid data being cleared". So if backup fails, we stop.
            logger.error("Aborting cleanup to prevent data loss.")
            return

    try:
        async with AsyncSessionLocal() as db:
            # Rebuild all documents, clear existing data
            # Note: The service itself might also try to clear data. 
            # We should update the service to also backup.
            await lightrag_service.rebuild_store(
                db, 
                exclude_filenames=[], # Do not exclude anything
                clear_existing=True # This will trigger service-level cleanup
            )
        logger.info("Full rebuild completed successfully.")
    except Exception as e:
        logger.error(f"Rebuild failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run())
