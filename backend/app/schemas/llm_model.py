from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class LLMModelBase(BaseModel):
    name: str
    provider: str
    model_id: str
    model_type: str = "text"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    is_active: bool = False


class LLMModelCreate(LLMModelBase):
    pass


class LLMModelUpdate(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    model_id: Optional[str] = None
    model_type: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    is_active: Optional[bool] = None


class LLMModelResponse(LLMModelBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LLMTestRequest(BaseModel):
    provider: str
    model_id: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None


class LLMTestResponse(BaseModel):
    success: bool
    message: str
