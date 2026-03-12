from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path

# Paths Configuration
# Assuming this file is in backend/app/services/rag/config/
# parents[0]=config, parents[1]=rag, parents[2]=services, parents[3]=app, parents[4]=backend
BACKEND_DIR = Path(__file__).resolve().parents[4]
DATA_DIR = BACKEND_DIR / "data"
LANCEDB_DIR = DATA_DIR / "lancedb"
LIGHTRAG_DIR = DATA_DIR / "lightrag_store"
UPLOAD_DIR = DATA_DIR / "temp"

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
LANCEDB_DIR.mkdir(parents=True, exist_ok=True)
LIGHTRAG_DIR.mkdir(parents=True, exist_ok=True)

class RagSettings(BaseSettings):
    CHUNK_SIZE: int = 1200
    CHUNK_OVERLAP: int = 120
    CHUNK_STRATEGY: str = "semantic"
    CHUNK_TOKENIZER: Optional[str] = None
    
    # LightRAG settings
    LIGHTRAG_MODE: str = "mix"
    
    # KG Query
    ENABLE_MOCK_KG_FALLBACK: bool = False
    
    class Config:
        env_prefix = "RAG_"

settings = RagSettings()
