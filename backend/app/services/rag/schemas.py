from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EmbedItem(BaseModel):
    id: Optional[str] = None
    text: str = Field(..., min_length=1)


class EmbedRequest(BaseModel):
    items: List[EmbedItem]
    batch_size: Optional[int] = 16


class EmbedResponse(BaseModel):
    vectors: List[List[float]]


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: Optional[int] = 5
    min_score: Optional[float] = 0.0


class SearchHit(BaseModel):
    title: Optional[str] = None
    score: float
    preview: Optional[str] = None
    url: Optional[str] = None
    page: Optional[int] = None


class SearchResponse(BaseModel):
    hits: List[SearchHit]


class AugmentRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    history: Optional[List[str]] = None
    top_k: Optional[int] = 5


class AugmentResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]


class HealthResponse(BaseModel):
    status: str
    llm_model: Optional[str] = None
    embed_model: Optional[str] = None
