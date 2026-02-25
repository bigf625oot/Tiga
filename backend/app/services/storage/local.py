import os
import shutil
import logging
from typing import Optional, BinaryIO
from app.services.storage.base import StorageProvider

logger = logging.getLogger(__name__)

class LocalStorage(StorageProvider):
    def __init__(self, upload_dir: str, base_url: str = "http://localhost:8000/uploads"):
        self.upload_dir = upload_dir
        self.base_url = base_url
        os.makedirs(self.upload_dir, exist_ok=True)

    async def upload_file(self, file_obj: BinaryIO, object_name: str) -> bool:
        try:
            file_path = os.path.join(self.upload_dir, object_name)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            file_obj.seek(0)
            with open(file_path, "wb") as f:
                shutil.copyfileobj(file_obj, f)
            logger.info(f"Successfully uploaded {object_name} to local storage at {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save locally: {e}")
            return False

    def upload_file_sync(self, key: str, data: bytes) -> str:
        try:
            file_path = os.path.join(self.upload_dir, key)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(data)
            return self.generate_presigned_url(key)
        except Exception as e:
            logger.error(f"Failed to save locally (sync): {e}")
            raise e

    def download_file(self, key: str, file_path: str):
        src = os.path.join(self.upload_dir, key)
        shutil.copy2(src, file_path)

    def delete_file(self, key: str) -> bool:
        try:
            file_path = os.path.join(self.upload_dir, key)
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        except Exception as e:
            logger.error(f"Local delete failed: {e}")
            return False

    def generate_presigned_url(self, key: str, expiration: int = 3600) -> Optional[str]:
        # Simple static URL mapping
        return f"{self.base_url}/{key}"
