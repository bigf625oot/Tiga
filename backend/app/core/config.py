from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Agentic：国产信创版Manus"
    API_V1_STR: str = "/api/v1"

    # Localization / 本地化
    LANGUAGE: str = "zh_CN"  # Default language: zh_CN, en_US / 默认语言

    # Logging / 日志
    LOG_LEVEL: str = "INFO"

    # Database / 数据库
    # Use SQLite for easier local setup if Postgres is not available
    # 如果 Postgres 不可用，使用 SQLite 进行便捷的本地设置
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

    # Redis / 缓存
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # S3 Object Storage / 对象存储
    STORAGE_TYPE: str = "local"  # local, s3, aliyun_oss
    S3_ENDPOINT_URL: Optional[str] = None  # For MinIO, etc. / 适用于 MinIO 等
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_NAME: str = "recordings"
    S3_REGION_NAME: str = "us-east-1"

    # Aliyun OSS (Overrides S3 configs if STORAGE_TYPE=aliyun_oss) / 阿里云 OSS 配置
    ALIYUN_OSS_ENDPOINT: str = "oss-cn-shanghai.aliyuncs.com"
    ALIYUN_OSS_BUCKET: Optional[str] = None  # Defaults to S3_BUCKET_NAME if None / 默认为 S3_BUCKET_NAME
    ALIYUN_OSS_ACCESS_KEY_ID: Optional[str] = None  # Defaults to ALIYUN_ACCESS_KEY_ID if None
    ALIYUN_OSS_ACCESS_KEY_SECRET: Optional[str] = None  # Defaults to ALIYUN_ACCESS_KEY_SECRET if None

    # LLM Defaults (can be overridden per request or via DB) / LLM 默认配置
    OPENAI_API_KEY: Optional[str] = None

    # Aliyun ASR / 阿里云语音识别
    ALIYUN_ACCESS_KEY_ID: Optional[str] = None
    ALIYUN_ACCESS_KEY_SECRET: Optional[str] = None
    ALIYUN_APP_KEY: Optional[str] = None

    # Aliyun Search Service (Search Agent) / 阿里云搜索服务
    ALIBABA_CLOUD_BEARER_TOKEN: Optional[str] = None
    ALIBABA_CLOUD_ENDPOINT: str = "cs.cn-beijing.aliyuncs.com"
    ALIBABA_CLOUD_PROTOCOL: str = "https"

    # Third Party (Search Agent) / 第三方搜索工具
    TAVILY_API_KEY: Optional[str] = None
    FIRECRAWL_API_KEY: Optional[str] = None

    # OpenClaw / 自动化爬虫引擎
    OPENCLAW_BASE_URL: Optional[str] = None  # ws:// or wss:// only
    OPENCLAW_WS_URL: Optional[str] = None  # ws:// or wss:// only
    OPENCLAW_GATEWAY_TOKEN: Optional[str] = None
    OPENCLAW_TOKEN: Optional[str] = None
    OPENCLAW_AGNO_KEY: Optional[str] = None
    OPENCLAW_AGNO_SECRET: Optional[str] = None
    OPENCLAW_ROUTING_SECRET: Optional[str] = None
    OPENCLAW_DEVICE_ID: Optional[str] = None
    OPENCLAW_DEVICE_PRIVATE_KEY: Optional[str] = None  # Base64 encoded Ed25519 private key
    OPENCLAW_LLM_MODEL: str = "gpt-3.5-turbo"  # Default model for OpenClaw fallbacks
    OPENCLAW_VERIFY_SSL: bool = True # Default to True, can be disabled via env
    
    # Proxy / 代理设置
    NO_PROXY: Optional[str] = None

    # DeepSeek / 深度求索
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"

    # E2B Sandbox / E2B 沙箱
    E2B_API_KEY: Optional[str] = None
    E2B_TEMPLATE_ID: Optional[str] = None

    # Graphiti Service / 知识图谱服务
    GRAPHITI_URL: str = "http://localhost:8000"

    # Security / 安全配置
    SECRET_KEY: str = "your-secret-key-here"  # Change this in production! / 生产环境请修改！
    MASTER_KEY: Optional[str] = None  # 32-byte base64 key for data source encryption / 数据源加密密钥

    # Retrieval Config / 检索配置
    RETRIEVAL_BACKEND: str = "local"
    VECTOR_BACKEND: str = "lancedb"
    GRAPH_BACKEND: str = "local"
    GRAPH_LANG: str = "zh"
    GRAPH_CACHE_TTL: int = 30
    RERANK_ENABLED: bool = False
    RERANK_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    MONITOR_ENABLED: bool = True
    # Chunking / 切分策略
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
    # Qdrant / 向量数据库
    QDRANT_URL: Optional[str] = None
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION: str = "kb_chunks"
    # Milvus / 向量数据库
    MILVUS_HOST: Optional[str] = None
    MILVUS_PORT: Optional[int] = None
    MILVUS_COLLECTION: str = "kb_chunks"
    # Neo4j / 图数据库
    NEO4J_URI: Optional[str] = None
    NEO4J_USER: Optional[str] = None
    NEO4J_PASSWORD: Optional[str] = None

    # Smart Ask Data (Text-to-SQL) / 智能问数
    KG_Q2S_ENABLE: bool = True

    class Config:
        # Support loading from .env in backend directory regardless of cwd
        # Try multiple locations: current dir, backend/, or parent/backend/
        env_file = [".env", "backend/.env", "../backend/.env"]
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()

# Apply network proxy settings globally
import os
if settings.NO_PROXY:
    os.environ["NO_PROXY"] = settings.NO_PROXY
    os.environ["no_proxy"] = settings.NO_PROXY
