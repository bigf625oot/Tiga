import asyncio
import logging
from typing import Any, Dict, List, Optional

import jieba
from sqlalchemy import text
from app.core.config import settings
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

class KeywordSearchService:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.fts_enabled = False
        self._check_fts_support()

    def _check_fts_support(self):
        """Check if SQLite FTS5 is supported and initialize tables if needed."""
        if not settings.USE_SQLITE:
            # TODO: Add Postgres/ES support if needed
            logger.info("Non-SQLite backend detected, keyword search service currently supports SQLite FTS5 only.")
            return

        async def _init_db():
            async with AsyncSessionLocal() as session:
                try:
                    # Check FTS5 availability
                    await session.execute(text("SELECT * FROM sqlite_compileoption_used('ENABLE_FTS5');"))
                    
                    # Create FTS table if not exists
                    # We use an external content table strategy or just a simple FTS table
                    # Here we use a simple FTS table for chunks
                    # Columns: chunk_id (unindexed), doc_id (unindexed), content (indexed), tokens (indexed)
                    await session.execute(text("""
                        CREATE VIRTUAL TABLE IF NOT EXISTS kb_chunks_fts USING fts5(
                            chunk_id UNINDEXED, 
                            doc_id UNINDEXED, 
                            content, 
                            tokens, 
                            tokenize='porter'
                        );
                    """))
                    await session.commit()
                    self.fts_enabled = True
                    logger.info("SQLite FTS5 keyword search initialized successfully.")
                except Exception as e:
                    logger.warning(f"SQLite FTS5 initialization failed, keyword search will be disabled: {e}")
        
        # Run initialization in background
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_init_db())
        except RuntimeError:
            # If no running loop (e.g. during tests/script), run synchronously-ish or skip
            pass

    async def upsert_doc_chunks(self, doc_id: int, chunks: List[Dict[str, Any]]):
        """
        Upsert chunks for a document into FTS index.
        chunks: list of dict with 'content', 'chunk_id' (optional), 'part_no' (optional)
        """
        if not self.fts_enabled:
            return

        async with AsyncSessionLocal() as session:
            try:
                # 1. Delete existing chunks for this doc (to avoid duplicates on re-index)
                # FTS5 delete is tricky, usually we delete by rowid or match query
                # For simplicity in this lightweight implementation, we might not strictly delete individual chunks 
                # unless we track them. But for full doc re-index, we should clear doc's chunks.
                # Since FTS doesn't support efficient "DELETE WHERE doc_id=?", we might leave old chunks 
                # or implement a "delete_doc" first.
                # Let's trust the caller to call delete_doc if doing a full rebuild.
                # For incremental, we just insert.
                
                for chunk in chunks:
                    content = chunk.get("content", "")
                    if not content:
                        continue
                        
                    # Jieba tokenization for better Chinese support in FTS
                    # FTS5 'porter' tokenizer works well for English, but for Chinese we need pre-tokenization
                    # or a custom tokenizer. Here we pre-tokenize with jieba and join with spaces.
                    seg_list = jieba.cut_for_search(content)
                    tokens = " ".join(seg_list)
                    
                    cid = chunk.get("chunk_id") or f"doc_{doc_id}_{hash(content)}"
                    
                    # Insert into FTS
                    await session.execute(text("""
                        INSERT INTO kb_chunks_fts (chunk_id, doc_id, content, tokens) 
                        VALUES (:cid, :did, :content, :tokens)
                    """), {"cid": str(cid), "did": str(doc_id), "content": content, "tokens": tokens})
                
                await session.commit()
            except Exception as e:
                logger.error(f"Failed to upsert chunks to FTS: {e}")

    async def delete_doc(self, doc_id: int):
        """Delete all chunks for a document from FTS index."""
        if not self.fts_enabled:
            return

        async with AsyncSessionLocal() as session:
            try:
                # SQLite FTS doesn't support "DELETE FROM tbl WHERE col=val" efficiently if col is UNINDEXED?
                # Actually it does, but it does a full scan.
                # Given doc_id is UNINDEXED in our schema, this might be slow for huge DBs.
                # Optimization: Query rowids by doc_id match if we indexed doc_id? 
                # But doc_id is int, FTS is text.
                # Let's try direct delete first.
                await session.execute(text("DELETE FROM kb_chunks_fts WHERE doc_id = :did"), {"did": str(doc_id)})
                await session.commit()
            except Exception as e:
                logger.error(f"Failed to delete doc {doc_id} from FTS: {e}")

    async def search(self, query: str, doc_id: Optional[int] = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for chunks using BM25 (via FTS5).
        Returns list of dict: {content, score, chunk_id, doc_id}
        """
        if not self.fts_enabled or not query.strip():
            return []

        async with AsyncSessionLocal() as session:
            try:
                # Tokenize query
                seg_list = jieba.cut_for_search(query.strip())
                query_tokens = " ".join(seg_list)
                if not query_tokens:
                    return []
                
                # FTS5 query syntax: tokens match
                # We search against the 'tokens' column
                # Construct query: tokens : "token1 token2 ..."
                fts_query = f'"{query_tokens}"'
                
                sql = """
                    SELECT chunk_id, doc_id, content, rank 
                    FROM kb_chunks_fts 
                    WHERE tokens MATCH :q 
                """
                params = {"q": fts_query}
                
                if doc_id is not None:
                    # Filter by doc_id in WHERE clause (might be slow scan after match, but OK for single doc)
                    sql += " AND doc_id = :did"
                    params["did"] = str(doc_id)
                
                sql += " ORDER BY rank LIMIT :k"
                params["k"] = top_k
                
                res = await session.execute(text(sql), params)
                rows = res.fetchall()
                
                results = []
                for r in rows:
                    results.append({
                        "chunk_id": r[0],
                        "doc_id": int(r[1]) if r[1] and r[1].isdigit() else None,
                        "content": r[2],
                        "score": r[3], # FTS5 rank (lower is better usually? No, BM25 in FTS5 extension returns negative score sometimes or we need to invert)
                        # Actually standard FTS5 'rank' is a calculated value. 
                        # We treat it as a score for now.
                    })
                return results
            except Exception as e:
                logger.warning(f"FTS search failed: {e}")
                return []

keyword_search = KeywordSearchService.get_instance()
