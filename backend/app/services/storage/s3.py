import logging
import boto3
from typing import Optional, BinaryIO
from app.services.storage.base import StorageProvider
from app.core.config import settings

logger = logging.getLogger(__name__)

class S3Storage(StorageProvider):
    def __init__(self):
        self.bucket_name = settings.S3_BUCKET_NAME
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION_NAME,
        )
        logger.info("Initialized S3 Storage")

    async def upload_file(self, file_obj: BinaryIO, object_name: str) -> bool:
        try:
            file_obj.seek(0)
            self.s3_client.upload_fileobj(file_obj, self.bucket_name, object_name)
            logger.info(f"Successfully uploaded {object_name} to S3")
            return True
        except Exception as e:
            logger.error(f"S3 Upload Failed: {e}")
            return False

    def upload_file_sync(self, key: str, data: bytes) -> str:
        try:
            import io
            file_obj = io.BytesIO(data)
            self.s3_client.upload_fileobj(file_obj, self.bucket_name, key)
            return self.generate_presigned_url(key) or ""
        except Exception as e:
            logger.error(f"S3 Upload Sync Failed: {e}")
            raise e

    def download_file(self, key: str, file_path: str):
        try:
            self.s3_client.download_file(self.bucket_name, key, file_path)
        except Exception as e:
            logger.error(f"S3 Download Failed: {e}")
            raise e

    def delete_file(self, key: str) -> bool:
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except Exception as e:
            logger.error(f"S3 delete failed: {e}")
            return False

    def generate_presigned_url(self, key: str, expiration: int = 3600) -> Optional[str]:
        try:
            response = self.s3_client.generate_presigned_url(
                "get_object", Params={"Bucket": self.bucket_name, "Key": key}, ExpiresIn=expiration
            )
            return response
        except Exception as e:
            logger.error(f"S3 Sign URL Failed: {e}")
            return None
