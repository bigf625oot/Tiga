"""
P10 Architecture: Node Model
First Principles: Nodes are stateful entities.
"""
from pydantic import BaseModel
class Node(BaseModel):
    id: str
    label: str
