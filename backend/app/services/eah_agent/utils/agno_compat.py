import inspect
from typing import Any, Dict, Callable


def filter_init_kwargs(init: Callable[..., Any], kwargs: Dict[str, Any]) -> Dict[str, Any]:
    try:
        sig = inspect.signature(init)
    except Exception:
        try:
            sig = inspect.signature(getattr(init, "__init__"))
        except Exception:
            return {}

    params = sig.parameters
    return {k: v for k, v in kwargs.items() if k in params and v is not None}
