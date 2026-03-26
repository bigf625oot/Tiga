from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict


_SENSITIVE_KEYS = {
    "api_key",
    "access_key",
    "access_key_id",
    "secret",
    "secret_key",
    "secret_access_key",
    "token",
    "bearer_token",
    "password",
    "private_key",
    "master_key",
    "openai_api_key",
}


def redact_secrets(value: Any) -> Any:
    if isinstance(value, dict):
        out: Dict[str, Any] = {}
        for k, v in value.items():
            lk = str(k).lower()
            if lk in _SENSITIVE_KEYS or lk.endswith("_api_key") or lk.endswith("_token") or lk.endswith("_secret"):
                out[k] = "******" if v is not None else None
                continue
            out[k] = redact_secrets(v)
        return out
    if isinstance(value, list):
        return [redact_secrets(x) for x in value]
    return value


def sanitize_agent_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    cloned = deepcopy(payload)
    return redact_secrets(cloned)
