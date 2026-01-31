import asyncio
import os
from app.services.lightrag_service import lightrag_service
from app.db.session import AsyncSessionLocal

async def check_lightrag():
    print("Initializing LightRAG...")
    async with AsyncSessionLocal() as db:
        await lightrag_service.ensure_initialized(db)
    
    print(f"Working Dir: {lightrag_service.working_dir}")
    print(f"RAG Instance: {lightrag_service.rag}")
    
    if lightrag_service.rag:
        print("Checking internal storages...")
        rag = lightrag_service.rag
        
        # Check Entity Storage
        try:
            entities = await rag.full_entities.get_all_data()
            print(f"Total Entities: {len(entities)}")
        except Exception as e:
            print(f"Error checking entities: {e}")
            
        # Check Relations
        try:
            relations = await rag.full_relations.get_all_data()
            print(f"Total Relations: {len(relations)}")
        except Exception as e:
            print(f"Error checking relations: {e}")
            
        # Check Graph File
        graph_file = os.path.join(lightrag_service.working_dir, "graph_chunk_entity_relation.graphml")
        if os.path.exists(graph_file):
            print(f"Graph file exists: {graph_file}")
            print(f"Size: {os.path.getsize(graph_file)} bytes")
        else:
            print(f"Graph file MISSING: {graph_file}")

if __name__ == "__main__":
    asyncio.run(check_lightrag())
