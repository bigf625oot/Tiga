import os
import time
import argparse
import pandas as pd
import pathway as pw
from typing import Dict, Any, List
from loguru import logger

# Import our custom sinks
from app.services.pathway.connectors.persistence import Neo4jSink, LightRAGSink, VectorObjectSink
from app.services.pathway.core.config import PathwayJobConfig

def run_persistence_pipeline(config_path: str):
    """
    End-to-end Pathway pipeline for high-performance data persistence.
    """
    logger.info("Starting Pathway Persistence Pipeline...")
    
    # 1. Load Configuration (Mocked for demonstration)
    # In a real scenario, this would load from a YAML file
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_auth = ("neo4j", os.getenv("NEO4J_PASSWORD", "password"))
    
    lightrag_path = "backend/data/lightrag_store"
    
    # 2. Define Data Source (Mocking 10GB scale via a stream of batches)
    # For demonstration, we'll use a smaller set but designed for scale
    # Mock generator that yields proper schema-compliant dictionaries
    class DataGenerator:
        def __iter__(self):
            for i in range(100):
                batch = []
                for j in range(1000):
                    row_id = f"id_{i}_{j}"
                    batch.append({
                        "id": row_id,
                        "entity_id": row_id,
                        "entity_type": "Person",
                        "name": f"User_{row_id}",
                        "description": "High-performance data persistence test row.",
                        "type": "node", 
                        "text": "This is a sample text chunk for vector embedding and object storage.",
                        "doc_id": f"doc_{i}",
                        "source_id": "benchmark_stream",
                        "relation_type": "RELATED_TO",
                        "weight": 1.0,
                        "source_id": row_id, # Reusing for rel test
                        "target_id": f"id_{i}_{j+1}"
                    })
                # Yield row by row or batch? pw.io.python.read expects iterable of rows if schema is provided,
                # or we can pass a list of dicts if using a connector that handles batches.
                # Actually pw.io.python.read expects an iterable of tuples or dicts (row-wise).
                for item in batch:
                    yield item

# ...
    # Schema definition is recommended for performance
    class InputSchema(pw.Schema):
        id: str
        entity_id: str
        entity_type: str
        name: str
        description: str
        type: str
        text: str
        doc_id: str
        relation_type: str
        weight: float
        target_id: str
        # source_id is duplicated in my previous edit, fixing it
        source_id: str

    table = pw.io.python.read(DataGenerator(), schema=InputSchema)
# ...

    # 3. Process / Clean (Optional)
    # table = table.with_columns(...)

    # 4. Multi-sink Persistence
    
    # Sink 1: Neo4j
    neo4j_sink = Neo4jSink(uri=neo4j_uri, auth=neo4j_auth)
    neo4j_sink.write(table, {})

    # Sink 2: LightRAG Store
    lightrag_sink = LightRAGSink(base_path=lightrag_path)
    lightrag_sink.write(table, {})

    # Sink 3: Vector + Object Storage
    vector_obj_sink = VectorObjectSink(
        vector_config={"type": "faiss", "path": "backend/data/vector_index"},
        object_store_config={"type": "minio", "bucket": "raw-data"}
    )
    vector_obj_sink.write(table, {})

    # 5. Execute Pipeline
    # pw.run() will start the reactive engine
    logger.info("Pipeline configured. Running...")
    try:
        # monitoring_dashboard_address helps track performance and memory
        pw.run(monitoring_dashboard_address="0.0.0.0:8082")
    except KeyboardInterrupt:
        logger.info("Pipeline stopped by user.")
    finally:
        neo4j_sink.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pathway Persistence Runner")
    parser.add_argument("--config", type=str, default="pathway.yml", help="Path to config file")
    args = parser.parse_args()
    
    run_persistence_pipeline(args.config)
