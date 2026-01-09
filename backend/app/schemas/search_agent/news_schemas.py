from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class NewsSearchRequest(BaseModel):
    keywords: List[str]
    # Tier 1: User specified government websites
    gov_sites: List[str] = []
    # Tier 2: Pre-defined authoritative websites (defaults provided, can be overridden)
    authoritative_sites: List[str] = [
        "xinhua.org", "people.com.cn", "chinadaily.com.cn", 
        "cctv.com", "gmw.cn"
    ]
    target_date: Optional[str] = None # Optional date filter
    days_back: int = 7 # Default to search last 7 days if no date provided
    max_results: int = 50

class CustomNewsSearchRequest(BaseModel):
    keywords: List[str]
    group_tag: str
    keyword_constraints: str
    result_requirements: str
    time_range: Optional[str] = None
    max_char_limit: int = 500

class NewsItem(BaseModel):
    trigger_keyword: str
    news_time: str
    url: str
    title: str
    content: str
    source: str
    tier: str # "core", "authoritative", "global"
    score: float

class NewsSearchResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
