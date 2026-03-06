
import asyncio
import logging
import os
import sys

import nest_asyncio

nest_asyncio.apply()

# Add backend directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.append(backend_dir)

# Configure logging
logging.basicConfig(level=logging.INFO)
logging.getLogger("lightrag").setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)

from app.db.session import AsyncSessionLocal
from app.services.rag.engines.lightrag import lightrag_engine
from lightrag.kg.shared_storage import get_namespace_data

async def run():
    # Get filenames from command line arguments
    args = sys.argv[1:]

    include_files = None
    if not args:
        logger.info("No arguments provided, using default hardcoded file.")
        include_files = ["中电金信大模型智能体平台介绍V0.3.pdf"]
    elif "--all" in args:
        logger.info("Targeting ALL files in the database.")
        include_files = None
    else:
        logger.info(f"Targeting files from CLI args: {args}")
        include_files = args

    logger.info("Starting knowledge base rebuild (chunking + vectorization)...")
    try:
        async with AsyncSessionLocal() as db:
            # Check pipeline status BEFORE rebuild
            # ps = await get_namespace_data("pipeline_status")
            # print(f"Pipeline Status BEFORE: {ps}")

            await lightrag_engine.rebuild_store(db, include_filenames=include_files, clear_existing=False)
            
            # Check pipeline status AFTER rebuild
            ps = await get_namespace_data("pipeline_status")
            print(f"Pipeline Status AFTER: {ps}")

            # Debugging status
            if lightrag_engine.rag:
                print("\n--- LightRAG Status Inspection ---")
                try:
                    import json
                    # Inspect Doc Status directly from JSON file
                    doc_status_path = os.path.join(lightrag_engine.working_dir, "kv_store_doc_status.json")
                    if os.path.exists(doc_status_path):
                        with open(doc_status_path, "r", encoding="utf-8") as f:
                            all_docs = json.load(f)
                        print(f"Total Docs in DocStatus: {len(all_docs)}")
                        for k, v in all_docs.items():
                            print(f"Doc: {k}, Status: {v.get('status')}, Error: {v.get('error')}")
                    else:
                        print(f"Doc status storage file not found at {doc_status_path}")
                except Exception as e:
                    print(f"Error inspecting doc status: {e}")
                
                try:
                    import json
                    # Inspect Text Chunks directly from JSON file
                    chunks_path = os.path.join(lightrag_engine.working_dir, "kv_store_text_chunks.json")
                    if os.path.exists(chunks_path):
                        with open(chunks_path, "r", encoding="utf-8") as f:
                            all_chunks = json.load(f)
                        print(f"Total Text Chunks: {len(all_chunks)}")
                    else:
                        print(f"Text chunks storage file not found at {chunks_path}")
                except Exception as e:
                    print(f"Error inspecting chunks: {e}")

        logger.info("Rebuild completed successfully.")
    except Exception as e:
        logger.error(f"Rebuild failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run())
