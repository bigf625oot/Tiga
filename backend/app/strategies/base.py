from abc import ABC, abstractmethod
from typing import List, AsyncGenerator, Any, Dict
from app.models.domain import MetadataModel, DataChunk

class BaseSource(ABC):
    """
    Abstract base class for all data source strategies.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """
        Verify connectivity to the data source.
        Returns a dictionary with success status and message.
        """
        pass

    @abstractmethod
    async def fetch_metadata(self) -> List[MetadataModel]:
        """
        Collect metadata from the data source (e.g., tables, files, endpoints).
        """
        pass

    @abstractmethod
    async def fetch_data(self, **kwargs) -> AsyncGenerator[DataChunk, None]:
        """
        Stream data chunks from the source.
        """
        pass
