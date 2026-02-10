import logging
import oss2
from typing import Optional, BinaryIO
from app.services.storage.base import StorageProvider
from app.core.config import settings

logger = logging.getLogger(__name__)

class AliyunOSSStorage(StorageProvider):
    def __init__(self):
        self.access_key = settings.ALIYUN_OSS_ACCESS_KEY_ID or settings.ALIYUN_ACCESS_KEY_ID
        self.access_secret = settings.ALIYUN_OSS_ACCESS_KEY_SECRET or settings.ALIYUN_ACCESS_KEY_SECRET
        self.endpoint = settings.ALIYUN_OSS_ENDPOINT
        self.bucket_name = settings.ALIYUN_OSS_BUCKET or settings.S3_BUCKET_NAME

        if not self.access_key or not self.access_secret:
            raise ValueError("Aliyun OSS credentials missing")

        # Ensure endpoint format
        if not self.endpoint.startswith("http"):
            self.endpoint = "https://" + self.endpoint

        auth = oss2.Auth(self.access_key.strip(), self.access_secret.strip())
        self.bucket = oss2.Bucket(auth, self.endpoint.strip(), self.bucket_name.strip())
        logger.info(f"Initialized Aliyun OSS Storage (Bucket: {self.bucket_name})")

    async def upload_file(self, file_obj: BinaryIO, object_name: str) -> bool:
        try:
            file_obj.seek(0)
            self.bucket.put_object(object_name, file_obj)
            logger.info(f"Successfully uploaded {object_name} to Aliyun OSS")
            return True
        except Exception as e:
            logger.error(f"Aliyun OSS Upload Failed: {e}")
            return False

    def upload_file_sync(self, key: str, data: bytes) -> str:
        try:
            self.bucket.put_object(key, data)
            # Public URL assumption or presigned
            return f"https://{self.bucket.bucket_name}.{settings.ALIYUN_OSS_ENDPOINT}/{key}"
        except Exception as e:
            logger.error(f"Failed to upload to OSS: {e}")
            raise e

    def download_file(self, key: str, file_path: str):
        try:
            self.bucket.get_object_to_file(key, file_path)
        except Exception as e:
            logger.error(f"Failed to download from OSS: {e}")
            raise e

    def delete_file(self, key: str) -> bool:
        try:
            self.bucket.delete_object(key)
            return True
        except Exception as e:
            logger.error(f"OSS delete failed: {e}")
            return False

    def generate_presigned_url(self, key: str, expiration: int = 3600) -> Optional[str]:
        try:
            return self.bucket.sign_url("GET", key, expiration)
        except Exception as e:
            logger.error(f"OSS Sign URL Failed: {e}")
            return None
