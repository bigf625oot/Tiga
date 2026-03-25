"""
P10 Architecture: Graph Builder
First Principles: Idempotent graph construction. Rebuilding the same document must yield the exact same topological structure.
"""
from abc import ABC, abstractmethod

class GraphBuilder(ABC):
    @abstractmethod
    def build_from_document(self, doc_id: str, content: str) -> None:
        pass
