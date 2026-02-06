from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ChatMessageBase(BaseModel):
    role: str
    content: str
    message_type: str = "text"
    meta_data: Optional[Dict[str, Any]] = None


class ChatMessageCreate(ChatMessageBase):
    pass


class ChatMessageResponse(ChatMessageBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ChatSessionBase(BaseModel):
    title: Optional[str] = None
    agent_id: Optional[str] = None


class ChatSessionCreate(ChatSessionBase):
    pass


class ChatSessionUpdate(BaseModel):
    title: Optional[str] = None
    agent_id: Optional[str] = None


class ChatSessionResponse(ChatSessionBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime]
    messages: List[ChatMessageResponse] = []

    class Config:
        from_attributes = True
