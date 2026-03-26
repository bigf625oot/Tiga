from __future__ import annotations

from typing import Any, TypeGuard

try:
    from agno.run import RunOutput as AgnoRunOutput  # type: ignore
except Exception:
    try:
        from agno.run.response import RunOutput as AgnoRunOutput  # type: ignore
    except Exception:
        AgnoRunOutput = None  # type: ignore


def is_run_output(x: Any) -> TypeGuard[Any]:
    if AgnoRunOutput is not None:
        return isinstance(x, AgnoRunOutput)
    return type(x).__name__ == "RunOutput"
