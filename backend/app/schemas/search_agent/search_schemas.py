from pydantic import BaseModel
from typing import Optional

class SearchRequest(BaseModel):
    query: str
    service_name: str = "default"
    app_name: str = "ops-web-search-001"

class SearchResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    message: Optional[str] = None
