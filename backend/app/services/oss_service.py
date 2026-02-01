import oss2
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class OSSService:
    def __init__(self):
        self.enabled = settings.STORAGE_TYPE == "aliyun_oss"
        if self.enabled:
            # Resolve keys with fallback to global Aliyun keys
            access_key_id = settings.ALIYUN_OSS_ACCESS_KEY_ID or settings.ALIYUN_ACCESS_KEY_ID
            access_key_secret = settings.ALIYUN_OSS_ACCESS_KEY_SECRET or settings.ALIYUN_ACCESS_KEY_SECRET
            
            if not access_key_id or not access_key_secret:
                logger.error("OSS configuration error: Access Key ID or Secret is missing. OSS service disabled.")
                self.enabled = False
                return

            try:
                # Ensure keys are stripped
                auth = oss2.Auth(
                    access_key_id.strip(), 
                    access_key_secret.strip()
                )
                self.bucket = oss2.Bucket(
                    auth, 
                    settings.ALIYUN_OSS_ENDPOINT.strip(), 
                    (settings.ALIYUN_OSS_BUCKET or settings.S3_BUCKET_NAME).strip()
                )
            except Exception as e:
                logger.error(f"Failed to initialize OSS service: {e}")
                self.enabled = False
    
    def upload_file(self, key: str, data: bytes) -> str:
        if not self.enabled:
            raise Exception("OSS storage is not enabled")
            
        try:
            self.bucket.put_object(key, data)
            # Generate URL (assuming public read or signed URL logic needed, but for now simple URL)
            # If bucket is private, we should use sign_url. Let's assume we want a persistent URL or signed.
            # For simplicity in this demo, we'll construct the URL.
            # Format: https://bucket-name.endpoint/key
            url = f"https://{self.bucket.bucket_name}.{settings.ALIYUN_OSS_ENDPOINT}/{key}"
            return url
        except Exception as e:
            logger.error(f"Failed to upload to OSS: {e}")
            raise e
    
    def upload_file_path(self, key: str, file_path: str) -> str:
        if not self.enabled:
            raise Exception("OSS storage is not enabled")
        try:
            self.bucket.put_object_from_file(key, file_path)
            url = f"https://{self.bucket.bucket_name}.{settings.ALIYUN_OSS_ENDPOINT}/{key}"
            return url
        except Exception as e:
            logger.error(f"Failed to upload file from path to OSS: {e}")
            raise e

    def delete_file(self, key: str):
        if not self.enabled:
            return
        try:
            self.bucket.delete_object(key)
        except Exception as e:
            logger.error(f"Failed to delete from OSS: {e}")
            # Don't raise, just log

    def download_file(self, key: str, file_path: str):
        if not self.enabled:
            raise Exception("OSS storage is not enabled")
        try:
            self.bucket.get_object_to_file(key, file_path)
        except Exception as e:
            logger.error(f"Failed to download from OSS: {e}")
            raise e

    def get_object_to_string(self, key: str) -> str:
        if not self.enabled:
            return ""
        try:
            result = self.bucket.get_object(key)
            return result.read().decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to read from OSS: {e}")
            return ""

oss_service = OSSService()
