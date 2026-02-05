
import asyncio
import os
import sys
from pathlib import Path

# Add backend to sys.path
backend_path = Path(__file__).resolve().parent / "backend"
sys.path.append(str(backend_path))

# Fix: Ensure we use the correct database file in backend/
db_path = backend_path / "recorder_v5.db"
if db_path.exists():
    # Set the environment variable before importing app modules
    # This overrides the default ./recorder_v5.db which would look in the root
    os.environ["SQLALCHEMY_DATABASE_URI"] = f"sqlite+aiosqlite:///{db_path}"
    print(f"DEBUG: Using database at {db_path}")

from app.services.lightrag_service import lightrag_service
from app.db.session import AsyncSessionLocal

async def main():
    print("Initializing LightRAG...")
    async with AsyncSessionLocal() as db:
        # Override db url for debug script to match config default if needed, 
        # but AsyncSessionLocal already uses settings.database_url which is sqlite+aiosqlite:///./recorder_v5.db
        # But wait, where is the DB file?
        # Config says: sqlite+aiosqlite:///./recorder_v5.db
        # Is the script running in the right CWD?
        # CWD is /Users/xucao/Documents/Python项目/taichi
        # Is recorder_v5.db there?
        pass
        
        # Manually initialize rag with the correct db
        from app.core.config import settings
        # ensure working directory for relative path
        import os
        # if recorder_v5.db is in backend/recorder_v5.db
        if not os.path.exists("recorder_v5.db") and os.path.exists("backend/recorder_v5.db"):
             os.chdir("backend")
             
        await lightrag_service.ensure_initialized(db)
    
    doc_id = 1
    query = "这份文档主要讲了什么？"
    
    print(f"Searching chunks for doc_id={doc_id} query='{query}'")
    chunks = lightrag_service.search_doc_chunks(doc_id, query, top_k=5)
    
    print(f"Found {len(chunks)} chunks")
    for i, c in enumerate(chunks):
        print(f"[{i+1}] Score: {c['score']} Path: {c['file_path']}")
        print(f"Content: {c['content'][:100]}...")
        print("-" * 20)

    # Check cache status
    print(f"Cache size: {len(lightrag_service._chunks_cache)}")
    print(f"Doc Map size: {len(lightrag_service._chunks_doc_map)}")
    
    # Check if doc#1 exists in map
    found = 0
    for k, v in lightrag_service._chunks_doc_map.items():
        if "doc#1:" in v:
            found += 1
    print(f"Chunks matching doc#1: in map: {found}")

if __name__ == "__main__":
    asyncio.run(main())
