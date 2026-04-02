from __future__ import annotations

import os
from copy import deepcopy
from typing import Any, Dict


def resolve_secret_refs(config: Dict[str, Any]) -> Dict[str, Any]:
    if not config:
        return {}
        
    has_env_keys = any(isinstance(k, str) and k.endswith("_env") for k in config.keys())
    if not has_env_keys:
        return config
        
    cfg = deepcopy(config)
    to_delete = []
    for k, v in list(cfg.items()):
        if not isinstance(k, str):
            continue
        if not k.endswith("_env"):
            continue
        if not isinstance(v, str) or not v.strip():
            continue
        env_value = os.environ.get(v.strip())
        if env_value is None:
            continue
        cfg[k[: -len("_env")]] = env_value
        to_delete.append(k)
    for k in to_delete:
        cfg.pop(k, None)
    return cfg
