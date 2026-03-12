from typing import Optional, List
from pydantic import BaseModel, Field
from agno.tools import Toolkit

# AWS S3
try:
    from agno.tools.aws_s3 import S3Tools as AgnoS3Tools
except ImportError:
    class AgnoS3Tools(Toolkit):
        def __init__(self, *args, **kwargs):
            raise ImportError("boto3 is required for S3Tools.")

class S3Tools(AgnoS3Tools):
    _name = "aws_s3"
    _label = "对象存储 (AWS S3)"
    _description = "管理 AWS S3 存储桶和文件"
    
    def __init__(self, bucket_name: str, aws_access_key_id: Optional[str] = None, aws_secret_access_key: Optional[str] = None, region_name: Optional[str] = None):
        super().__init__(bucket_name=bucket_name, aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name=region_name)

    class Config(BaseModel):
        bucket_name: str = Field(..., description="S3 Bucket Name")
        aws_access_key_id: Optional[str] = Field(None, description="AWS Access Key ID")
        aws_secret_access_key: Optional[str] = Field(None, description="AWS Secret Access Key")
        region_name: Optional[str] = Field(None, description="AWS Region")

# AWS Lambda
try:
    from agno.tools.aws_lambda import AWSLambdaTools as AgnoAWSLambdaTools
except ImportError:
    class AgnoAWSLambdaTools(Toolkit):
        def __init__(self, *args, **kwargs):
            raise ImportError("boto3 is required for AWSLambdaTools.")

class AWSLambdaTools(AgnoAWSLambdaTools):
    _name = "aws_lambda"
    _label = "无服务器函数 (AWS Lambda)"
    _description = "调用 AWS Lambda 函数"

    def __init__(self, region_name: str, aws_access_key_id: Optional[str] = None, aws_secret_access_key: Optional[str] = None):
        super().__init__(region_name=region_name, aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)

    class Config(BaseModel):
        region_name: str = Field(..., description="AWS Region")
        aws_access_key_id: Optional[str] = Field(None, description="AWS Access Key ID")
        aws_secret_access_key: Optional[str] = Field(None, description="AWS Secret Access Key")
