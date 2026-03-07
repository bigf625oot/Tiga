from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

import pathway as pw

class BaseSource(ABC):
    @abstractmethod
    def read(self, config: Dict[str, Any]) -> pw.Table:
        pass
    
    def discover_schema(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Optional method for schema discovery."""
        raise NotImplementedError("Schema discovery not implemented for this source")

class BaseSink(ABC):
    @abstractmethod
    def write(self, table: pw.Table, config: Dict[str, Any]) -> None:
        pass
