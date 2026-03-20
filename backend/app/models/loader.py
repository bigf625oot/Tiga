from __future__ import annotations

import importlib
import pkgutil

import app.models


def import_all_models() -> None:
    for module in pkgutil.iter_modules(app.models.__path__, app.models.__name__ + "."):
        importlib.import_module(module.name)
