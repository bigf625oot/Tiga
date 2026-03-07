from typing import Callable, Dict, Any, Optional
import pathway as pw
from app.services.pathway.core.exceptions import OperatorError
from app.core.logger import logger

class OperatorRegistry:
    _instance = None
    _operators: Dict[str, Callable] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OperatorRegistry, cls).__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, name: str):
        """
        Decorator to register an operator function.
        Usage:
            @OperatorRegistry.register("my_operator")
            def my_operator_func(table, config): ...
        """
        def decorator(func: Callable):
            if name in cls._operators:
                logger.warning(f"Overwriting existing operator: {name}")
            cls._operators[name] = func
            return func
        return decorator

    @classmethod
    def get_operator(cls, name: str) -> Callable[[pw.Table, Dict[str, Any]], pw.Table]:
        """
        Get an operator function by name.
        """
        if name not in cls._operators:
            raise OperatorError(f"Operator not found: {name}")
        return cls._operators[name]

    @classmethod
    def list_operators(cls):
        return list(cls._operators.keys())

# Global instance for easy access if needed, though class methods are used.
registry = OperatorRegistry()
