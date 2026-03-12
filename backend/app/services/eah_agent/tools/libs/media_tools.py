from typing import Optional, List
try:
    from agno.tools.youtube import YouTubeTools as AgnoYouTubeTools
except ImportError:
    class AgnoYouTubeTools:
        def __init__(self, *args, **kwargs):
            raise ImportError("youtube-transcript-api is required. Please install it.")
from pydantic import BaseModel, Field

class YouTubeTools(AgnoYouTubeTools):
    _name = "youtube"
    _label = "视频解析 (YouTube)"
    _description = "获取 YouTube 视频字幕和元数据"
    """
    使用 YouTubeTools 获取视频信息。
    """
    def __init__(self):
        super().__init__()

    class Config(BaseModel):
        pass
