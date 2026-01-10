import shutil
import os
from pathlib import Path
from typing import List, Dict, Any
from fastapi import UploadFile

from agno.knowledge.knowledge import Knowledge
from agno.vectordb.lancedb import LanceDb
from agno.knowledge.embedder.openai import OpenAIEmbedder
from app.core.config import settings
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
        # Configure Embedder (support DeepSeek via OpenAI compatible interface)
        embedder_config = {
            "api_key": settings.OPENAI_API_KEY,
        }
        
        # If DeepSeek settings are present, override configuration
        if settings.DEEPSEEK_API_KEY:
             embedder_config["api_key"] = settings.DEEPSEEK_API_KEY
             embedder_config["base_url"] = settings.DEEPSEEK_BASE_URL
             embedder_config["id"] = "deepseek-embed" # DeepSeek Embedding Model
             embedder_config["dimensions"] = 1024 # DeepSeek embedding dimensions

        self.vector_db = LanceDb(
            table_name="vectors",
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

    def delete_document(self, filename: str):
        try:
            # Try deleting by name (usually filename if added by path)
            self.knowledge.vector_db.delete_by_name(filename)
        except Exception as e:
            logger.error(f"Error deleting document {filename}: {e}")
            pass 
        return {"status": "deleted"}

kb_service = KnowledgeBaseService.get_instance()
