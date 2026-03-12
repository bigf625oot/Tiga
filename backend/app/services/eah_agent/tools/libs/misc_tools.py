from typing import Optional, List, Any
from pydantic import BaseModel, Field
from agno.tools import Toolkit

# Sleep
try:
    from agno.tools.sleep import SleepTools as AgnoSleepTools
except ImportError:
    class AgnoSleepTools(Toolkit):
        def __init__(self, *args, **kwargs):
            pass

class SleepTools(AgnoSleepTools):
    _name = "sleep"
    _label = "休眠 (Sleep)"
    _description = "暂停执行一段时间"
    
    def __init__(self):
        super().__init__()

# Resend
try:
    from agno.tools.resend import ResendTools as AgnoResendTools
except ImportError:
    class AgnoResendTools(Toolkit):
        def __init__(self, *args, **kwargs):
            raise ImportError("resend is required for ResendTools.")

class ResendTools(AgnoResendTools):
    _name = "resend"
    _label = "Resend 邮件"
    _description = "使用 Resend API 发送邮件"
    
    def __init__(self, api_key: str):
        super().__init__(api_key=api_key)

    class Config(BaseModel):
        api_key: str = Field(..., description="Resend API Key")

# Fal
try:
    from agno.tools.fal import FalTools as AgnoFalTools
except ImportError:
    class AgnoFalTools(Toolkit):
        def __init__(self, *args, **kwargs):
            raise ImportError("fal-client is required for FalTools.")

class FalTools(AgnoFalTools):
    _name = "fal"
    _label = "Fal AI"
    _description = "运行 Fal AI 媒体生成模型"
    
    def __init__(self, api_key: str):
        super().__init__(api_key=api_key)

    class Config(BaseModel):
        api_key: str = Field(..., description="Fal API Key")
