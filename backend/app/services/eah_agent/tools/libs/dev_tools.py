from typing import Optional, List
try:
    from agno.tools.github import GithubTools as AgnoGithubTools
except ImportError:
    class AgnoGithubTools:
        def __init__(self, *args, **kwargs):
            raise ImportError("PyGithub is required. Please install it.")
            
from pydantic import BaseModel, Field

class GithubTools(AgnoGithubTools):
    _name = "github"
    _label = "代码仓库 (GitHub)"
    _description = "搜索 GitHub 仓库、代码和管理 Issue"
    """
    使用 GithubTools 操作 GitHub。
    """
    def __init__(self, access_token: str):
        super().__init__(access_token=access_token)

    class Config(BaseModel):
        access_token: str = Field(..., description="GitHub Personal Access Token")
