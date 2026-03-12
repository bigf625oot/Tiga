from typing import Optional, List, Any
from pydantic import BaseModel, Field
from agno.tools import Toolkit

# Discord
try:
    from agno.tools.discord import DiscordTools as AgnoDiscordTools
except ImportError:
    class AgnoDiscordTools(Toolkit):
        def __init__(self, *args, **kwargs):
            raise ImportError("discord.py is required for DiscordTools.")

class DiscordTools(AgnoDiscordTools):
    _name = "discord"
    _label = "Discord"
    _description = "发送 Discord 消息和管理频道"
    
    def __init__(self, bot_token: str, channel_id: Optional[str] = None):
        super().__init__(bot_token=bot_token, channel_id=channel_id)

    class Config(BaseModel):
        bot_token: str = Field(..., description="Discord Bot Token")
        channel_id: Optional[str] = Field(None, description="Default Channel ID")

# Slack
try:
    from agno.tools.slack import SlackTools as AgnoSlackTools
except ImportError:
    class AgnoSlackTools(Toolkit):
        def __init__(self, *args, **kwargs):
            raise ImportError("slack_sdk is required for SlackTools.")

class SlackTools(AgnoSlackTools):
    _name = "slack"
    _label = "Slack"
    _description = "发送 Slack 消息和文件"
    
    def __init__(self, token: str, default_channel: Optional[str] = None):
        super().__init__(token=token, default_channel=default_channel)

    class Config(BaseModel):
        token: str = Field(..., description="Slack Bot Token")
        default_channel: Optional[str] = Field(None, description="Default Channel Name or ID")

# Telegram
try:
    from agno.tools.telegram import TelegramTools as AgnoTelegramTools
except ImportError:
    class AgnoTelegramTools(Toolkit):
        def __init__(self, *args, **kwargs):
            raise ImportError("python-telegram-bot is required for TelegramTools.")

class TelegramTools(AgnoTelegramTools):
    _name = "telegram"
    _label = "Telegram"
    _description = "发送 Telegram 消息"
    
    def __init__(self, token: str, chat_id: Optional[str] = None):
        super().__init__(token=token, chat_id=chat_id)

    class Config(BaseModel):
        token: str = Field(..., description="Telegram Bot Token")
        chat_id: Optional[str] = Field(None, description="Default Chat ID")

# Email
try:
    from agno.tools.email import EmailTools as AgnoEmailTools
except ImportError:
    class AgnoEmailTools(Toolkit):
        def __init__(self, *args, **kwargs):
            pass

class EmailTools(AgnoEmailTools):
    _name = "email"
    _label = "邮件 (SMTP)"
    _description = "发送和接收电子邮件"
    
    def __init__(self, 
                 receiver_email: Optional[str] = None, 
                 sender_email: Optional[str] = None, 
                 sender_name: Optional[str] = None, 
                 sender_password: Optional[str] = None, 
                 smtp_server: Optional[str] = "smtp.gmail.com", 
                 smtp_port: Optional[int] = 587):
        super().__init__(
            receiver_email=receiver_email,
            sender_email=sender_email,
            sender_name=sender_name,
            sender_password=sender_password,
            smtp_server=smtp_server,
            smtp_port=smtp_port
        )

    class Config(BaseModel):
        sender_email: str = Field(..., description="Sender Email Address")
        sender_password: str = Field(..., description="Sender Email Password/App Password")
        receiver_email: Optional[str] = Field(None, description="Default Receiver Email")
        smtp_server: str = Field("smtp.gmail.com", description="SMTP Server Host")
        smtp_port: int = Field(587, description="SMTP Server Port")

# Twilio
try:
    from agno.tools.twilio import TwilioTools as AgnoTwilioTools
except ImportError:
    class AgnoTwilioTools(Toolkit):
        def __init__(self, *args, **kwargs):
            raise ImportError("twilio is required for TwilioTools.")

class TwilioTools(AgnoTwilioTools):
    _name = "twilio"
    _label = "短信 (Twilio)"
    _description = "发送短信和 WhatsApp 消息"
    
    def __init__(self, account_sid: str, auth_token: str, from_number: str):
        super().__init__(account_sid=account_sid, auth_token=auth_token, from_number=from_number)

    class Config(BaseModel):
        account_sid: str = Field(..., description="Twilio Account SID")
        auth_token: str = Field(..., description="Twilio Auth Token")
        from_number: str = Field(..., description="Twilio Phone Number")

# Zoom
try:
    from agno.tools.zoom import ZoomTools as AgnoZoomTools
except ImportError:
    class AgnoZoomTools(Toolkit):
        def __init__(self, *args, **kwargs):
            raise ImportError("requests is required for ZoomTools.")

class ZoomTools(AgnoZoomTools):
    _name = "zoom"
    _label = "Zoom"
    _description = "管理 Zoom 会议"
    
    def __init__(self, account_id: str, client_id: str, client_secret: str):
        super().__init__(account_id=account_id, client_id=client_id, client_secret=client_secret)

    class Config(BaseModel):
        account_id: str = Field(..., description="Zoom Account ID")
        client_id: str = Field(..., description="Zoom Client ID")
        client_secret: str = Field(..., description="Zoom Client Secret")
