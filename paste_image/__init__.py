import os

import streamlit.components.v1 as components

_FRONTEND = os.path.join(os.path.dirname(__file__), "frontend")
_paste_image = components.declare_component("paste_image", path=_FRONTEND)


def paste_image(label: str = "Paste a screenshot", key: str | None = None):
    """Clipboard / drag-drop image capture. Returns dict with data/type/name or None."""
    return _paste_image(label=label, key=key, default=None)
