"""
Agent Memory Interface

Defines the abstract interface for memory operations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from .models import MemoryUnit, SessionContext

class AgentMemoryInterface(ABC):
    
    @abstractmethod
    async def add_memory(self, session_id: str, memory: MemoryUnit, ttl: Optional[int] = None) -> str:
        """
        Add a memory unit to the store.
        Returns the memory_id.
        """
        pass

    @abstractmethod
    async def get_memory(self, memory_id: str) -> Optional[MemoryUnit]:
        """
        Retrieve a specific memory unit.
        """
        pass

    @abstractmethod
    async def get_session_context(self, session_id: str, limit: int = 20) -> List[MemoryUnit]:
        """
        Get recent memories for a session (chronological order).
        """
        pass

    @abstractmethod
    async def search_memory(self, query: str, session_id: Optional[str] = None, limit: int = 10) -> List[MemoryUnit]:
        """
        Semantic/Keyword search for memories.
        """
        pass

    @abstractmethod
    async def delete_memory(self, memory_id: str):
        """
        Delete a memory unit.
        """
        pass
