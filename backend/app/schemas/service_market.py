from typing import List, Literal

from pydantic import BaseModel


MarketItemType = Literal["mcp", "skill"]


class MarketInstallRequest(BaseModel):
    type: MarketItemType
    id: str


class MarketInstalledResponse(BaseModel):
    mcp: List[str] = []
    skill: List[str] = []

