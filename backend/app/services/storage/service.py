import os
import logging
from typing import Optional, BinaryIO
from app.core.config import settings
from app.services.storage.base import StorageProvider
from app.services.storage.local import LocalStorage
from app.services.storage.oss import AliyunOSSStorage
from app.services.storage.s3 import S3Storage

logger = logging.getLogger(__name__)

class StorageService:
    _instance = None
    provider: StorageProvider = None

    def __init__(self):
        self._init_provider()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _init_provider(self):
        storage_type = (settings.STORAGE_TYPE or "local").lower()
        
        try:
            if storage_type == "aliyun_oss":
                self.provider = AliyunOSSStorage()
            elif storage_type == "s3":
                self.provider = S3Storage()
            else:
                backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
                upload_dir = os.path.join(backend_dir, "data", "storage")
                self.provider = LocalStorage(upload_dir)
        except Exception as e:
            logger.error(f"Failed to initialize storage provider {storage_type}: {e}. Falling back to local.")
            backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            upload_dir = os.path.join(backend_dir, "data", "storage")
            self.provider = LocalStorage(upload_dir)

    async def upload_file(self, file_obj: BinaryIO, object_name: str) -> bool:
        return await self.provider.upload_file(file_obj, object_name)

    def upload_file_sync(self, key: str, data: bytes) -> str:
        return self.provider.upload_file_sync(key, data)
    
    def download_file(self, key: str, file_path: str):
        return self.provider.download_file(key, file_path)

    def upload_file_path(self, key: str, file_path: str) -> Optional[str]:
        """Upload a file from local path."""
        try:
            with open(file_path, "rb") as f:
                # Some providers might optimize this, but reading into memory/stream is generic
                # If provider has specific method, we could use it.
                # AliyunOSSStorage has put_object_from_file usually?
                # For now, just read and upload.
                # Wait, upload_file expects file-like object?
                # My base interface says upload_file(file_obj: BinaryIO, object_name: str)
                # But provider implementations might vary.
                # Let's use upload_file_sync if it takes bytes, or handle async.
                
                # Check provider capabilities
                if hasattr(self.provider, "upload_file_from_path"):
                     return self.provider.upload_file_from_path(key, file_path)
                
                # Fallback to reading bytes
                data = f.read()
                return self.provider.upload_file_sync(key, data)
        except Exception as e:
            logger.error(f"Failed to upload file from path {file_path}: {e}")
            raise

    def delete_file(self, key: str) -> bool:
        return self.provider.delete_file(key)

    def generate_presigned_url(self, key: str, expiration: int = 3600) -> Optional[str]:
        return self.provider.generate_presigned_url(key, expiration)

    # Legacy support
    @property
    def bucket(self):
        """Backwards compatibility for direct bucket access (deprecated)."""
        if isinstance(self.provider, AliyunOSSStorage):
            return self.provider.bucket
        return None

storage_service = StorageService.get_instance()
