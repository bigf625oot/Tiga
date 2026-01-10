from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Recorder AI"
    API_V1_STR: str = "/api/v1"
    
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
            return "sqlite+aiosqlite:///./recorder_v5.db"
            
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    
    # S3 Object Storage
    STORAGE_TYPE: str = "local" # local, s3, aliyun_oss
    S3_ENDPOINT_URL: Optional[str] = None # For MinIO, etc.
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_NAME: str = "recordings"
    S3_REGION_NAME: str = "us-east-1"
    
    # Aliyun OSS (Overrides S3 configs if STORAGE_TYPE=aliyun_oss)
    ALIYUN_OSS_ENDPOINT: str = "oss-cn-shanghai.aliyuncs.com" 
    ALIYUN_OSS_BUCKET: Optional[str] = None # Defaults to S3_BUCKET_NAME if None
    ALIYUN_OSS_ACCESS_KEY_ID: Optional[str] = None # Defaults to ALIYUN_ACCESS_KEY_ID if None
    ALIYUN_OSS_ACCESS_KEY_SECRET: Optional[str] = None # Defaults to ALIYUN_ACCESS_KEY_SECRET if None

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

    # DeepSeek
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"

    # Graphiti Service
    GRAPHITI_URL: str = "http://localhost:8000"


    class Config:
        env_file = ".env"

settings = Settings()
