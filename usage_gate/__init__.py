"""Browser-persisted visitor usage counters (localStorage)."""

from __future__ import annotations

import os
from typing import Any

import streamlit.components.v1 as components

_FRONTEND = os.path.join(os.path.dirname(__file__), "frontend")
_usage_store = components.declare_component("usage_store", path=_FRONTEND)


def usage_store(write: dict[str, Any] | None = None, key: str | None = None):
    """Read (and optionally write) visitor usage from browser localStorage."""
    return _usage_store(write=write, key=key, default=None)
