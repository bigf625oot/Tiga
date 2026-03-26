"""
P10 Architecture: Edge Model
First Principles: Edges define directional semantic relationships.
"""
from pydantic import BaseModel
class Edge(BaseModel):
    source: str
    target: str
    relation: str
