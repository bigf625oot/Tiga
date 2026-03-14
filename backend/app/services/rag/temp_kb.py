import numpy as np
import asyncio
import logging
from typing import List, Dict, Any
from pathlib import Path
from app.services.rag.knowledge.service import kb_service
from app.services.rag.knowledge.parser import parse_local_file_chunks

logger = logging.getLogger(__name__)

class TempKnowledgeBase:
    _instance = None
    
    def __init__(self):
        # storage: {session_id: {'chunks': [], 'embeddings': np.array}}
        self.storage: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def add_document(self, session_id: str, file_path: str):
        # Run CPU-bound/IO-bound tasks in thread
        try:
            await asyncio.to_thread(self._add_document_sync, session_id, file_path)
        except Exception as e:
            logger.error(f"Failed to add temp document {file_path}: {e}")

    def _add_document_sync(self, session_id: str, file_path: str):
        pages = parse_local_file_chunks(file_path)
        if not pages:
            return
            
        all_chunks_text = []
        all_metas = []
        
        # Chunk per page to keep page number
        for p in pages:
            page_num = p.get("page")
            text = p.get("text", "")
            if not text: continue
            
            page_chunks = kb_service._chunk_text(text)
            all_chunks_text.extend(page_chunks)
            all_metas.extend([{"page": page_num}] * len(page_chunks))
            
        if not all_chunks_text:
            return
            
        embeddings = kb_service._embed_texts(all_chunks_text)
        if not embeddings:
            return
            
        embeddings_np = np.array(embeddings)
        
        if session_id not in self.storage:
            self.storage[session_id] = {'chunks': [], 'embeddings': None}
            
        session_data = self.storage[session_id]
        
        # Offset for chunk IDs
        start_idx = len(session_data['chunks'])
        
        new_chunks = []
        for i, c in enumerate(all_chunks_text):
            new_chunks.append({
                'content': c, 
                'source': file_path,
                'chunk_id': f"temp_{start_idx + i}",
                'page': all_metas[i].get("page")
            })
        
        session_data['chunks'].extend(new_chunks)
        
        if session_data['embeddings'] is None:
            session_data['embeddings'] = embeddings_np
        else:
            session_data['embeddings'] = np.vstack((session_data['embeddings'], embeddings_np))
        
        logger.info(f"Added temp document {file_path} with {len(new_chunks)} chunks for session {session_id}")

    async def search(self, session_id: str, query: str, top_k: int = 5):
        try:
            return await asyncio.to_thread(self._search_sync, session_id, query, top_k)
        except Exception as e:
            logger.error(f"Temp KB search failed: {e}")
            return []

    def _search_sync(self, session_id: str, query: str, top_k: int = 5):
        if session_id not in self.storage or self.storage[session_id]['embeddings'] is None:
            return []
            
        session_data = self.storage[session_id]
        embeddings = session_data['embeddings']
        chunks = session_data['chunks']
        
        query_embedding_list = kb_service._embed_texts([query])
        if not query_embedding_list:
            return []
            
        query_vec = np.array(query_embedding_list[0])
        
        # Cosine Similarity
        norm_docs = np.linalg.norm(embeddings, axis=1)
        norm_query = np.linalg.norm(query_vec)
        
        if norm_query == 0:
            return []
            
        sims = np.dot(embeddings, query_vec) / (norm_docs * norm_query + 1e-10)
        
        # Top K
        k = min(top_k, len(chunks))
        if k == 0: return []
        
        indices = np.argsort(sims)[::-1][:k]
        
        results = []
        for idx in indices:
            score = float(sims[idx])
            if score < 0.3: continue # threshold
            chunk = chunks[idx]
            results.append({
                "title": Path(chunk['source']).name,
                "url": "", # Temp file has no URL
                "page": chunk.get('page'),
                "score": score,
                "preview": chunk['content'][:200],
                "chunk_id": chunk['chunk_id'],
                "doc_id": 0,
                "node_id": None,
                "content": chunk['content']
            })
            
        return results

    def clear_session(self, session_id: str):
        if session_id in self.storage:
            del self.storage[session_id]
            logger.info(f"Cleared temp KB for session {session_id}")
