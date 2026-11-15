"""opensituas — CLI e libreria Python per il SITUAS (ISTAT)."""

from __future__ import annotations

from .api import catalog, cerca_codice, count, get, info, storia
from .base import SituasError
from .cli import app, main

__all__ = [
    "catalog", "info", "get", "count", "storia", "cerca_codice",
    "SituasError", "app", "main",
]
__version__ = "0.1.0"
