from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from app.core.i18n import _


class ChatMessageBase(BaseModel):
    role: str = Field(..., description=_("Role of the message sender (user, assistant, system)"))
    content: str = Field(..., description=_("Content of the message"))
    message_type: str = Field("text", description=_("Type of the message (text, image, etc.)"))
    meta_data: Optional[Dict[str, Any]] = Field(None, description=_("Additional metadata for the message"))


class ChatMessageCreate(ChatMessageBase):
    pass


class ChatMessageResponse(ChatMessageBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ChatSessionBase(BaseModel):
    title: Optional[str] = Field(None, description=_("Title of the chat session"))
    agent_id: Optional[str] = Field(None, description=_("ID of the agent used in this session"))
    mode: Optional[str] = Field("chat", description=_("Mode of the session (chat, task, etc.)"))
    workflow_state: Optional[Dict[str, Any]] = Field(None, description=_("Current state of the workflow"))


class ChatSessionCreate(ChatSessionBase):
    pass


class ChatSessionUpdate(BaseModel):
    title: Optional[str] = None
    agent_id: Optional[str] = None
    mode: Optional[str] = None
    workflow_state: Optional[Dict[str, Any]] = None


class ChatSessionResponse(ChatSessionBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime]
    messages: List[ChatMessageResponse] = []

    class Config:
        from_attributes = True
