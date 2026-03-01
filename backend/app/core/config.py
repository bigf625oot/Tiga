from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Taichi Agent"
    API_V1_STR: str = "/api/v1"

    # Logging
    LOG_LEVEL: str = "INFO"

    # Database
    # Use SQLite for easier local setup if Postgres is not available
    USE_SQLITE: bool = True
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "recorder_db"
    SQLALCHEMY_DATABASE_URI: Optional[str] = None

    @property
    def database_url(self) -> str:
        if self.SQLALCHEMY_DATABASE_URI:
            return self.SQLALCHEMY_DATABASE_URI

        if self.USE_SQLITE:
            import os
            # Ensure we use an absolute path to avoid CWD issues
            # Base it on the backend directory (where main.py usually is)
            # This file is in backend/app/core/config.py -> backend is 3 levels up
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(base_dir, "recorder_v5.db")
            # Windows path handling for SQLAlchemy URL
            if os.name == 'nt':
                 db_path = db_path.replace('\\', '/')
            return f"sqlite+aiosqlite:///{db_path}"

        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None



    TASK_MODE_CACHE_TTL_SECONDS: int = 30
    TASK_MODE_LOG_RETENTION_NORMAL_DAYS: int = 30
    TASK_MODE_LOG_RETENTION_IMPORTANT_DAYS: int = 365

    # S3 Object Storage
    STORAGE_TYPE: str = "local"  # local, s3, aliyun_oss
    S3_ENDPOINT_URL: Optional[str] = None  # For MinIO, etc.
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_NAME: str = "recordings"
    S3_REGION_NAME: str = "us-east-1"

    # Aliyun OSS (Overrides S3 configs if STORAGE_TYPE=aliyun_oss)
    ALIYUN_OSS_ENDPOINT: str = "oss-cn-shanghai.aliyuncs.com"
    ALIYUN_OSS_BUCKET: Optional[str] = None  # Defaults to S3_BUCKET_NAME if None
    ALIYUN_OSS_ACCESS_KEY_ID: Optional[str] = None  # Defaults to ALIYUN_ACCESS_KEY_ID if None
    ALIYUN_OSS_ACCESS_KEY_SECRET: Optional[str] = None  # Defaults to ALIYUN_ACCESS_KEY_SECRET if None

    # LLM Defaults (can be overridden per request or via DB)
    OPENAI_API_KEY: Optional[str] = None

    # Aliyun ASR
    ALIYUN_ACCESS_KEY_ID: Optional[str] = None
    ALIYUN_ACCESS_KEY_SECRET: Optional[str] = None
    ALIYUN_APP_KEY: Optional[str] = None

    # Aliyun Search Service (Search Agent)
    ALIBABA_CLOUD_BEARER_TOKEN: Optional[str] = None
    ALIBABA_CLOUD_ENDPOINT: str = "cs.cn-beijing.aliyuncs.com"
    ALIBABA_CLOUD_PROTOCOL: str = "https"

    # Third Party (Search Agent)
    TAVILY_API_KEY: Optional[str] = None
    FIRECRAWL_API_KEY: Optional[str] = None

    # OpenClaw
    OPENCLAW_BASE_URL: Optional[str] = None  # No default, strictly read from env
    OPENCLAW_WS_URL: Optional[str] = None
    OPENCLAW_GATEWAY_TOKEN: Optional[str] = None
    OPENCLAW_TOKEN: Optional[str] = None
    OPENCLAW_DEVICE_ID: Optional[str] = None
    OPENCLAW_DEVICE_PRIVATE_KEY: Optional[str] = None  # Base64 encoded Ed25519 private key
    OPENCLAW_LLM_MODEL: str = "gpt-3.5-turbo"  # Default model for OpenClaw fallbacks
    
    # Proxy
    NO_PROXY: Optional[str] = None

    # DeepSeek
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"

    # E2B Sandbox
    E2B_API_KEY: Optional[str] = None
    E2B_TEMPLATE_ID: Optional[str] = None

    # Graphiti Service
    GRAPHITI_URL: str = "http://localhost:8000"

    # Security
    SECRET_KEY: str = "your-secret-key-here"  # Change this in production!

    # Retrieval Config
    RETRIEVAL_BACKEND: str = "local"
    VECTOR_BACKEND: str = "lancedb"
    GRAPH_BACKEND: str = "local"
    GRAPH_LANG: str = "zh"
    GRAPH_CACHE_TTL: int = 30
    RERANK_ENABLED: bool = False
    RERANK_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    MONITOR_ENABLED: bool = True
    # Chunking
    CHUNK_STRATEGY: str = "semantic"
    CHUNK_SIZE: int = 1200
    CHUNK_OVERLAP: int = 120
    CHUNK_PREVIEW_LEN: int = 400
    CHUNK_TOKENIZER: Optional[str] = None
    CONTEXT_TOKENS_LIMIT: int = 6000
    GRAPH_EXTRACT_MAX_TOKENS: int = 4096
    CHUNK_EXTRACT_MAX: int = 100
    KG_MAX_ITEMS: int = 200
    OCR_ENABLED: bool = False
    QA_SYSTEM_PROMPT: str = ""
    QA_SYSTEM_PROMPT_FILE: str = "backend/prompts/qa_system.md"
    # Qdrant
    QDRANT_URL: Optional[str] = None
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION: str = "kb_chunks"
    # Milvus
    MILVUS_HOST: Optional[str] = None
    MILVUS_PORT: Optional[int] = None
    MILVUS_COLLECTION: str = "kb_chunks"
    # Neo4j
    NEO4J_URI: Optional[str] = None
    NEO4J_USER: Optional[str] = None
    NEO4J_PASSWORD: Optional[str] = None

    class Config:
        env_file = ".env"


settings = Settings()

# Apply network proxy settings globally
import os
if settings.NO_PROXY:
    os.environ["NO_PROXY"] = settings.NO_PROXY
    os.environ["no_proxy"] = settings.NO_PROXY
