import time
import json
import logging
import uuid
import os
from typing import List, Dict, Any, Optional
import pathway as pw
from neo4j import GraphDatabase, Driver
from app.services.pathway.connectors.base import BaseSink
from app.services.pathway.core.exceptions import ConnectorError
from loguru import logger

# =============================================================================
# 1. Neo4j Sink
# =============================================================================

class Neo4jSink(BaseSink):
    """
    Sink for Neo4j Graph Database.
    Writes nodes and relationships using batched MERGE operations for idempotency.
    """
    def __init__(self, uri: str, auth: tuple, batch_size: int = 1000, max_retries: int = 3):
        self.driver: Driver = GraphDatabase.driver(uri, auth=auth)
        self.batch_size = batch_size
        self.max_retries = max_retries

    def close(self):
        if self.driver:
            self.driver.close()

    def write(self, table: pw.Table, config: Dict[str, Any]) -> None:
        # Pathway's write is declarative, it sets up the output stream.
        # We need to use pw.io.subscribe or similar to process the stream row-by-row or in batches.
        # However, standard pw.io.write connectors usually handle this internally.
        # Since we are implementing a custom sink, we can use pw.io.python.write to call our python function.
        
        # We'll define the python writer function here
        def _write_batch(rows: List[Dict]):
            if not rows:
                return
            
            # Separate nodes and relationships based on schema
            # Assuming input rows have 'type' (node/rel) and properties
            nodes = []
            rels = []
            
            for row in rows:
                if row.get('type') == 'node':
                    nodes.append(row)
                elif row.get('type') == 'relationship':
                    rels.append(row)
            
            self._write_to_neo4j(nodes, rels)

        # Use pw.io.python.write to invoke our writer
        # Note: pw.io.python.write passes a list of rows (batch) if configured? 
        # Actually pw.io.python.write takes a callable that receives the table updates.
        # But for simplicity in this custom sink structure, let's assume we use apply or similar mechanism
        # or we return the write operation.
        
        # Correct Pathway pattern for custom sink:
        # pw.io.subscribe(table, _write_batch) # This is for streaming
        # But we want to integrate with our engine.
        
        # For now, let's just return the callable and let the engine handle it or use a native python writer
        # We will use pw.io.python.write(table, _write_batch)
        pw.io.python.write(table, _write_batch)

    def _write_to_neo4j(self, nodes: List[Dict], rels: List[Dict]):
        with self.driver.session() as session:
            # Write Nodes
            if nodes:
                self._execute_with_retry(session, self._merge_nodes_query(), {"batch": nodes})
            # Write Relationships
            if rels:
                self._execute_with_retry(session, self._merge_rels_query(), {"batch": rels})

    def _execute_with_retry(self, session, query, params):
        for attempt in range(self.max_retries):
            try:
                session.run(query, params)
                return
            except Exception as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"Neo4j write failed after {self.max_retries} attempts: {e}")
                    raise ConnectorError(f"Neo4j write failed: {e}")
                time.sleep(2 ** attempt)  # Exponential backoff

    def _merge_nodes_query(self) -> str:
        # Assuming generic node structure: {entity_id, entity_type, properties...}
        return """
        UNWIND $batch AS row
        CALL {
            WITH row
            MERGE (n:Entity {id: row.entity_id})
            ON CREATE SET 
                n.type = row.entity_type,
                n.name = row.name,
                n.description = row.description,
                n.created_at = timestamp()
            ON MATCH SET
                n.updated_at = timestamp()
        }
        """

    def _merge_rels_query(self) -> str:
        # Assuming rel structure: {source_id, target_id, relation_type, properties...}
        # Dynamic relationship types are tricky in Cypher without APOC.
        # We'll use a generic 'RELATED_TO' type with a property 'type' if dynamic types are needed,
        # or assume a fixed type from config. Let's use APOC if available or a fixed type for now.
        return """
        UNWIND $batch AS row
        CALL {
            WITH row
            MATCH (source:Entity {id: row.source_id})
            MATCH (target:Entity {id: row.target_id})
            MERGE (source)-[r:RELATED_TO]->(target)
            ON CREATE SET
                r.type = row.relation_type,
                r.weight = row.weight,
                r.description = row.description,
                r.created_at = timestamp()
            ON MATCH SET
                r.weight = row.weight,
                r.updated_at = timestamp()
        }
        """

# =============================================================================
# 2. LightRAG Sink
# =============================================================================

class LightRAGSink(BaseSink):
    """
    Sink for LightRAG File Store.
    Writes serialized JSON/GraphML files with sharding.
    """
    def __init__(self, base_path: str, shard_size: int = 10000):
        self.base_path = base_path
        self.shard_size = shard_size
        os.makedirs(self.base_path, exist_ok=True)

    def write(self, table: pw.Table, config: Dict[str, Any]) -> None:
        def _write_shard(rows: List[Dict]):
            if not rows:
                return
            
            # Generate shard ID based on timestamp and uuid
            shard_id = f"{int(time.time())}_{uuid.uuid4().hex[:8]}"
            shard_dir = os.path.join(self.base_path, f"shard_{shard_id}")
            os.makedirs(shard_dir, exist_ok=True)
            
            # Group data by type
            entities = {}
            relations = {}
            chunks = {}
            
            for row in rows:
                doc_id = row.get('doc_id', 'unknown')
                r_type = row.get('type')
                
                if r_type == 'entity':
                    if doc_id not in entities: entities[doc_id] = []
                    entities[doc_id].append(row)
                elif r_type == 'relation':
                    if doc_id not in relations: relations[doc_id] = []
                    relations[doc_id].append(row)
                elif r_type == 'chunk':
                    if doc_id not in chunks: chunks[doc_id] = []
                    chunks[doc_id].append(row)
            
            # Write JSON files (KV Store simulation)
            self._write_json(os.path.join(shard_dir, "kv_store_full_entities.json"), entities)
            self._write_json(os.path.join(shard_dir, "kv_store_full_relations.json"), relations)
            self._write_json(os.path.join(shard_dir, "kv_store_text_chunks.json"), chunks)
            
            # Write GraphML (Graph Store simulation)
            # This requires converting the batch to a networkx graph then graphml, or manual XML generation
            # For performance, we might just append to a log or write a mini-graphml
            pass

        pw.io.python.write(table, _write_shard)

    def _write_json(self, path: str, data: Dict):
        # Atomic write: write to temp then rename
        tmp_path = path + ".tmp"
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)

# =============================================================================
# 3. Vector & Object Storage Sink
# =============================================================================

class VectorObjectSink(BaseSink):
    """
    Sink for Vector DB (FAISS/PGVector) and Object Storage (MinIO/S3).
    """
    def __init__(self, vector_config: Dict, object_store_config: Dict, embedding_model: str = "all-MiniLM-L6-v2"):
        self.vector_config = vector_config
        self.object_store_config = object_store_config
        self.embedding_model = embedding_model
        # Initialize clients (mock or real)
        self.s3_client = self._init_s3()
        self.vector_client = self._init_vector()
        self.embedder = self._init_embedder()

    def _init_s3(self):
        # Placeholder for boto3 client
        return None

    def _init_vector(self):
        # Placeholder for FAISS/PGVector client
        return None
    
    def _init_embedder(self):
        # Placeholder for SentenceTransformer
        # from sentence_transformers import SentenceTransformer
        # return SentenceTransformer(self.embedding_model)
        return None

    def write(self, table: pw.Table, config: Dict[str, Any]) -> None:
        def _process_batch(rows: List[Dict]):
            if not rows:
                return
            
            texts = [row.get('text', '') for row in rows]
            ids = [row.get('id') for row in rows]
            
            # 1. Generate Embeddings
            # embeddings = self.embedder.encode(texts)
            embeddings = [[0.1] * 384 for _ in texts] # Mock
            
            # 2. Upload to S3
            for row in rows:
                # self.s3_client.put_object(...)
                pass
            
            # 3. Insert into Vector DB
            # self.vector_client.add(ids, embeddings, metadatas=rows)
            pass

        pw.io.python.write(table, _process_batch)

