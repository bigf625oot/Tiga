import shutil
import os
from pathlib import Path
from typing import List, Dict, Any
from fastapi import UploadFile

from agno.knowledge.knowledge import Knowledge
from agno.vectordb.lancedb import LanceDb
from agno.knowledge.embedder.openai import OpenAIEmbedder
from app.core.config import settings
from app.models.llm_model import LLMModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)

# Paths
DATA_DIR = Path("backend/data")
LANCEDB_DIR = DATA_DIR / "lancedb"
UPLOAD_DIR = DATA_DIR / "uploads"

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
LANCEDB_DIR.mkdir(parents=True, exist_ok=True)

class KnowledgeBaseService:
    _instance = None

    def __init__(self):
        # Default Configuration (Env vars)
        self._init_default()

    def _init_default(self):
        # Configure Embedder (support DeepSeek via OpenAI compatible interface)
        embedder_config = {
            "api_key": settings.OPENAI_API_KEY or "dummy",
            "id": "openai-embedding",
            "dimensions": 1536
        }
        
        # If DeepSeek settings are present, override configuration
        if settings.DEEPSEEK_API_KEY:
            embedder_config["api_key"] = settings.DEEPSEEK_API_KEY
            embedder_config["base_url"] = settings.DEEPSEEK_BASE_URL
            embedder_config["id"] = "deepseek-embed"
            embedder_config["dimensions"] = 1024

        table_name = f"vectors_{embedder_config.get('id','embed')}_{embedder_config.get('dimensions',1536)}"

        self.vector_db = LanceDb(
            table_name=table_name,
            uri=str(LANCEDB_DIR),
            embedder=OpenAIEmbedder(**embedder_config)
        )
        
        self.knowledge = Knowledge(
            name="Recorder Knowledge Base",
            vector_db=self.vector_db,
        )

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def reload_config(self, db: AsyncSession):
        """
        Reload embedder configuration from database (LLMModel)
        """
        try:
            # Find active embedding model
            # Note: We check for model_type='embedding' or provider='embedding' just in case
            # But based on user input, it should be model_type='embedding'
            result = await db.execute(
                select(LLMModel)
                .filter(LLMModel.model_type == "embedding", LLMModel.is_active == True)
                .order_by(LLMModel.updated_at.desc())
            )
            model = result.scalars().first()
            
            if model:
                logger.info(f"Reloading Knowledge Base with Embedding Model: {model.name} ({model.model_id})")
                
                embedder_config = {
                    "api_key": model.api_key,
                    "id": model.model_id,
                }
                
                if model.base_url:
                    embedder_config["base_url"] = model.base_url
                
                base = (embedder_config.get("base_url") or "").lower()
                mid = (embedder_config.get("id") or "").lower()
                if "open.bigmodel.cn" in base:
                    base_norm = base.replace("/v4/embeddings", "/v4").rstrip("/")
                    embedder_config["base_url"] = base_norm
                    if mid.startswith("embedding-3"):
                        embedder_config["dimensions"] = 2048
                else:
                    embedder_config.setdefault("dimensions", 1536)
                
                table_name = f"vectors_{embedder_config.get('id','embed')}_{embedder_config.get('dimensions',1536)}"
                self.vector_db = LanceDb(
                    table_name=table_name,
                    uri=str(LANCEDB_DIR),
                    embedder=OpenAIEmbedder(**embedder_config)
                )
                self.knowledge = Knowledge(
                    name="Recorder Knowledge Base",
                    vector_db=self.vector_db,
                )
            else:
                logger.info("No active embedding model found in DB. Keeping default configuration.")
                
        except Exception as e:
            logger.error(f"Failed to reload Knowledge Base config: {e}")

    def index_document(self, file_path: str):
        """
        Index a local file into the knowledge base.
        """
        try:
            self.knowledge.add_content(path=file_path)
            return True
        except Exception as e:
            logger.error(f"Error indexing document {file_path}: {e}")
            raise e

    def search(self, query: str, allowed_names: List[str] | None = None, min_score: float = 0.0, top_k: int = 5):
        refs: List[Dict[str, Any]] = []
        filtered: List[Dict[str, Any]] = []
        try:
            results = self.vector_db.search(query, limit=top_k)
            for r in results:
                meta = None
                name = None
                score = 0.0
                content = None
                if isinstance(r, dict):
                    meta = r.get("metadata") or {}
                    name = (meta.get("name") or meta.get("filename") or r.get("name"))
                    score = r.get("score") or 0.0
                    content = r.get("content") or meta.get("text")
                else:
                    meta = getattr(r, "metadata", {}) or {}
                    name = meta.get("name") or meta.get("filename") or getattr(r, "name", None)
                    score = getattr(r, "score", 0.0) or 0.0
                    content = getattr(r, "content", None) or meta.get("text")
                if allowed_names and name and name not in allowed_names:
                    filtered.append({"title": name, "score": score})
                    continue
                if score is not None and score < (min_score or 0.0):
                    filtered.append({"title": name, "score": score})
                    continue
                refs.append({
                    "title": name or "",
                    "url": (meta or {}).get("url"),
                    "page": (meta or {}).get("page"),
                    "score": score,
                    "preview": (content or "")[:200]
                })
        except Exception as e:
            logger.warning(f"Search error: {e}")
        return refs, filtered

    def delete_document(self, filename: str):
        try:
            # Try deleting by name (usually filename if added by path)
            self.knowledge.vector_db.delete_by_name(filename)
        except Exception as e:
            logger.error(f"Error deleting document {filename}: {e}")
            pass 
        return {"status": "deleted"}

kb_service = KnowledgeBaseService.get_instance()
