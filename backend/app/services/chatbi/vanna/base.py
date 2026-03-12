from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """
    Abstract base class for all tools.
    """

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """
        Execute the tool with the given arguments.
        """
        pass
