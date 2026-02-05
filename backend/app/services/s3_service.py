import boto3
from botocore.exceptions import NoCredentialsError
from app.core.config import settings
import io
import os
import shutil
import logging
import oss2

logger = logging.getLogger(__name__)

class S3Service:
    def __init__(self):
        self.storage_type = settings.STORAGE_TYPE.lower()
        # Use absolute path for backend/data/storage to avoid CWD dependency
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.upload_dir = os.path.join(backend_dir, "data", "storage")
        
        # Initialize clients based on type
        self.s3_client = None
        self.oss_bucket = None
        
        if self.storage_type == "aliyun_oss":
            self._init_aliyun_oss()
        elif self.storage_type == "s3":
            self._init_s3()
        else:
            self.storage_type = "local" # Fallback
            os.makedirs(self.upload_dir, exist_ok=True)
            logger.info("Using Local Storage")

    def _init_s3(self):
        try:
            self.bucket_name = settings.S3_BUCKET_NAME
            self.s3_client = boto3.client(
                's3',
                endpoint_url=settings.S3_ENDPOINT_URL,
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY,
                region_name=settings.S3_REGION_NAME
            )
            logger.info("Initialized S3 Storage")
        except Exception as e:
            logger.error(f"S3 Init Failed: {e}, falling back to local")
            self.storage_type = "local"

    def _init_aliyun_oss(self):
        try:
            access_key = settings.ALIYUN_OSS_ACCESS_KEY_ID or settings.ALIYUN_ACCESS_KEY_ID
            access_secret = settings.ALIYUN_OSS_ACCESS_KEY_SECRET or settings.ALIYUN_ACCESS_KEY_SECRET
            endpoint = settings.ALIYUN_OSS_ENDPOINT
            self.bucket_name = settings.ALIYUN_OSS_BUCKET or settings.S3_BUCKET_NAME
            
            if not access_key or not access_secret:
                raise ValueError("Aliyun OSS credentials missing")
            
            # Ensure endpoint starts with http:// or https://
            if not endpoint.startswith("http://") and not endpoint.startswith("https://"):
                endpoint = "https://" + endpoint
                
            auth = oss2.Auth(access_key, access_secret)
            self.oss_bucket = oss2.Bucket(auth, endpoint, self.bucket_name)
            logger.info(f"Initialized Aliyun OSS Storage (Bucket: {self.bucket_name})")
        except Exception as e:
            logger.error(f"Aliyun OSS Init Failed: {e}, falling back to local")
            self.storage_type = "local"

    async def upload_file(self, file_obj, object_name):
        logger.info(f"Starting upload for {object_name} to {self.storage_type}...")
        if self.storage_type == "local":
            try:
                file_path = os.path.join(self.upload_dir, object_name)
                file_obj.seek(0)
                with open(file_path, "wb") as f:
                    shutil.copyfileobj(file_obj, f)
                logger.info(f"Successfully uploaded {object_name} to local storage at {file_path}")
                return True
            except Exception as e:
                logger.error(f"Failed to save locally: {e}")
                return False
        
        elif self.storage_type == "aliyun_oss":
            try:
                file_obj.seek(0)
                self.oss_bucket.put_object(object_name, file_obj)
                logger.info(f"Successfully uploaded {object_name} to Aliyun OSS")
                return True
            except Exception as e:
                logger.error(f"Aliyun OSS Upload Failed: {e}")
                return False

        elif self.storage_type == "s3":
            try:
                file_obj.seek(0)
                self.s3_client.upload_fileobj(file_obj, self.bucket_name, object_name)
                logger.info(f"Successfully uploaded {object_name} to S3")
                return True
            except Exception as e:
                logger.error(f"S3 Upload Failed: {e}")
                return False
        
        return False

    def generate_presigned_url(self, object_name, expiration=3600):
        logger.info(f"Generating presigned URL for {object_name}...")
        if self.storage_type == "local":
            # Return local static URL
            # Note: This requires the frontend/client to be able to access this host
            url = f"http://localhost:8000/uploads/{object_name}"
            logger.info(f"Generated local URL: {url}")
            return url

        elif self.storage_type == "aliyun_oss":
            try:
                # oss2 sign_url method
                url = self.oss_bucket.sign_url('GET', object_name, expiration)
                logger.info(f"Generated OSS URL: {url}")
                return url
            except Exception as e:
                logger.error(f"OSS Sign URL Failed: {e}")
                return None

        elif self.storage_type == "s3":
            try:
                response = self.s3_client.generate_presigned_url('get_object',
                                                                Params={'Bucket': self.bucket_name,
                                                                        'Key': object_name},
                                                                ExpiresIn=expiration)
                logger.info(f"Generated S3 URL: {response}")
                return response
            except Exception as e:
                logger.error(f"S3 Sign URL Failed: {e}")
                return None
        
        return None

    def delete_file(self, object_name):
        if self.storage_type == "local":
            try:
                file_path = os.path.join(self.upload_dir, object_name)
                if os.path.exists(file_path):
                    os.remove(file_path)
                return True
            except Exception as e:
                logger.error(f"Local delete failed: {e}")
                return False

        elif self.storage_type == "aliyun_oss":
            try:
                self.oss_bucket.delete_object(object_name)
                return True
            except Exception as e:
                logger.error(f"OSS delete failed: {e}")
                return False

        elif self.storage_type == "s3":
            try:
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=object_name)
                return True
            except Exception as e:
                logger.error(f"S3 delete failed: {e}")
                return False
        
        return False

s3_service = S3Service()
