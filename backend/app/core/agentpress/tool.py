from typing import Any, Dict, Optional

class Tool:
    """
    Base class for all tools.
    """
    def __init__(self):
        pass

    def run(self, **kwargs) -> Any:
        raise NotImplementedError("Subclasses must implement run()")

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @property
    def description(self) -> str:
        return "No description provided."
