from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field


class LLMModelBase(BaseModel):
    name: str
    provider: str
    model_id: str
    model_type: str = "text"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    api_version: Optional[str] = None
    
    # Capabilities
    context_length: int = 4096
    max_output_tokens: int = 2048
    supports_vision: bool = False
    supports_tools: bool = True
    supports_json_mode: bool = True
    
    # Inference Params
    temperature: float = 0.7
    top_p: float = 1.0
    extra_params: Optional[Dict[str, Any]] = {}
    
    # Pricing
    input_token_price: float = 0.0
    output_token_price: float = 0.0
    
    is_active: bool = False
    priority: int = 0


class LLMModelCreate(LLMModelBase):
    pass


class LLMModelUpdate(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    model_id: Optional[str] = None
    model_type: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    api_version: Optional[str] = None
    
    context_length: Optional[int] = None
    max_output_tokens: Optional[int] = None
    supports_vision: Optional[bool] = None
    supports_tools: Optional[bool] = None
    supports_json_mode: Optional[bool] = None
    
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    extra_params: Optional[Dict[str, Any]] = None
    
    input_token_price: Optional[float] = None
    output_token_price: Optional[float] = None
    
    is_active: Optional[bool] = None
    priority: Optional[int] = None


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
