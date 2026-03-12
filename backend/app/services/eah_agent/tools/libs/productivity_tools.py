from typing import Optional, List, Any
from pydantic import BaseModel, Field
from agno.tools import Toolkit

# Notion
try:
    from agno.tools.notion import NotionTools as AgnoNotionTools
except ImportError:
    class AgnoNotionTools(Toolkit):
        def __init__(self, *args, **kwargs):
            raise ImportError("notion-client is required for NotionTools.")

class NotionTools(AgnoNotionTools):
    _name = "notion"
    _label = "Notion"
    _description = "管理 Notion 页面和数据库"
    
    def __init__(self, auth_token: str):
        super().__init__(auth_token=auth_token)

    class Config(BaseModel):
        auth_token: str = Field(..., description="Notion Integration Token")

# Jira
try:
    from agno.tools.jira import JiraTools as AgnoJiraTools
except ImportError:
    class AgnoJiraTools(Toolkit):
        def __init__(self, *args, **kwargs):
            raise ImportError("jira is required for JiraTools.")

class JiraTools(AgnoJiraTools):
    _name = "jira"
    _label = "Jira"
    _description = "管理 Jira 项目和 Issue"
    
    def __init__(self, server_url: str, username: str, token: str):
        super().__init__(server_url=server_url, username=username, token=token)

    class Config(BaseModel):
        server_url: str = Field(..., description="Jira Server URL")
        username: str = Field(..., description="Jira Username/Email")
        token: str = Field(..., description="Jira API Token")

# Linear
try:
    from agno.tools.linear import LinearTools as AgnoLinearTools
except ImportError:
    class AgnoLinearTools(Toolkit):
        def __init__(self, *args, **kwargs):
            raise ImportError("requests is required for LinearTools.")

class LinearTools(AgnoLinearTools):
    _name = "linear"
    _label = "Linear"
    _description = "管理 Linear 问题追踪"
    
    def __init__(self, api_key: str):
        super().__init__(api_key=api_key)

    class Config(BaseModel):
        api_key: str = Field(..., description="Linear API Key")

# Trello
try:
    from agno.tools.trello import TrelloTools as AgnoTrelloTools
except ImportError:
    class AgnoTrelloTools(Toolkit):
        def __init__(self, *args, **kwargs):
            raise ImportError("py-trello is required for TrelloTools.")

class TrelloTools(AgnoTrelloTools):
    _name = "trello"
    _label = "Trello"
    _description = "管理 Trello 看板和卡片"
    
    def __init__(self, api_key: str, token: str):
        super().__init__(api_key=api_key, token=token)

    class Config(BaseModel):
        api_key: str = Field(..., description="Trello API Key")
        token: str = Field(..., description="Trello Token")

# Todoist
try:
    from agno.tools.todoist import TodoistTools as AgnoTodoistTools
except ImportError:
    class AgnoTodoistTools(Toolkit):
        def __init__(self, *args, **kwargs):
            raise ImportError("todoist-api-python is required for TodoistTools.")

class TodoistTools(AgnoTodoistTools):
    _name = "todoist"
    _label = "Todoist"
    _description = "管理 Todoist 任务"
    
    def __init__(self, api_key: str):
        super().__init__(api_key=api_key)

    class Config(BaseModel):
        api_key: str = Field(..., description="Todoist API Key")

# Google Calendar
try:
    from agno.tools.google_calendar import GoogleCalendarTools as AgnoGoogleCalendarTools
except ImportError:
    class AgnoGoogleCalendarTools(Toolkit):
        def __init__(self, *args, **kwargs):
            raise ImportError("google-auth-oauthlib is required for GoogleCalendarTools.")

class GoogleCalendarTools(AgnoGoogleCalendarTools):
    _name = "google_calendar"
    _label = "谷歌日历 (Google Calendar)"
    _description = "管理 Google 日历事件"
    
    def __init__(self, credentials_path: str = "credentials.json", token_path: str = "token.json"):
        super().__init__(credentials_path=credentials_path, token_path=token_path)

    class Config(BaseModel):
        credentials_path: str = Field("credentials.json", description="Path to client_secret.json")
        token_path: str = Field("token.json", description="Path to token.json")

# Google Sheets
try:
    from agno.tools.google_sheets import GoogleSheetsTools as AgnoGoogleSheetsTools
except ImportError:
    class AgnoGoogleSheetsTools(Toolkit):
        def __init__(self, *args, **kwargs):
            raise ImportError("google-api-python-client is required for GoogleSheetsTools.")

class GoogleSheetsTools(AgnoGoogleSheetsTools):
    _name = "google_sheets"
    _label = "谷歌表格 (Google Sheets)"
    _description = "读写 Google Sheets 数据"
    
    def __init__(self, credentials_path: str = "credentials.json", token_path: str = "token.json"):
        super().__init__(credentials_path=credentials_path, token_path=token_path)

    class Config(BaseModel):
        credentials_path: str = Field("credentials.json", description="Path to client_secret.json")
        token_path: str = Field("token.json", description="Path to token.json")
