from typing import Optional, List, Any
from pydantic import BaseModel, Field
from agno.tools import Toolkit

# Google Drive
try:
    from agno.tools.google_drive import GoogleDriveTools as AgnoGoogleDriveTools
except ImportError:
    class AgnoGoogleDriveTools(Toolkit):
        def __init__(self, *args, **kwargs):
            raise ImportError("google-api-python-client is required for GoogleDriveTools.")

class GoogleDriveTools(AgnoGoogleDriveTools):
    _name = "google_drive"
    _label = "谷歌云端硬盘 (Google Drive)"
    _description = "管理 Google Drive 文件"
    
    def __init__(self, credentials_path: str = "credentials.json", token_path: str = "token.json"):
        super().__init__(credentials_path=credentials_path, token_path=token_path)

    class Config(BaseModel):
        credentials_path: str = Field("credentials.json", description="Path to client_secret.json")
        token_path: str = Field("token.json", description="Path to token.json")

# Newspaper4k
try:
    from agno.tools.newspaper4k import Newspaper4kTools as AgnoNewspaper4kTools
except ImportError:
    class AgnoNewspaper4kTools(Toolkit):
        def __init__(self, *args, **kwargs):
            raise ImportError("newspaper4k is required for Newspaper4kTools.")

class Newspaper4kTools(AgnoNewspaper4kTools):
    _name = "newspaper4k"
    _label = "新闻提取 (Newspaper4k)"
    _description = "提取新闻文章内容和元数据"
    
    def __init__(self):
        super().__init__()

# Pubmed
try:
    from agno.tools.pubmed import PubmedTools as AgnoPubmedTools
except ImportError:
    class AgnoPubmedTools(Toolkit):
        def __init__(self, *args, **kwargs):
            raise ImportError("pubmed is required for PubmedTools.")

class PubmedTools(AgnoPubmedTools):
    _name = "pubmed"
    _label = "医学文献 (PubMed)"
    _description = "搜索生物医学文献"
    
    def __init__(self):
        super().__init__()
