"""Per-visitor usage limits to control xAI API spend on public launches."""

from __future__ import annotations

import os
import uuid
from typing import Any

import streamlit as st

DEFAULT_MAX_ANALYSES = 2
DEFAULT_MAX_RESUME_DOWNLOADS = 2


def _secret_int(name: str, default: int) -> int:
    env_val = os.getenv(name)
    if env_val and str(env_val).strip().lstrip("-").isdigit():
        return max(0, int(str(env_val).strip()))
    try:
        val = st.secrets.get(name)
        if val is not None and str(val).strip().lstrip("-").isdigit():
            return max(0, int(str(val).strip()))
    except Exception:
        pass
    return default


def max_analyses() -> int:
    return _secret_int("MAX_ANALYSES_PER_VISITOR", DEFAULT_MAX_ANALYSES)


def max_resume_downloads() -> int:
    return _secret_int("MAX_RESUME_DOWNLOADS", DEFAULT_MAX_RESUME_DOWNLOADS)


def _default_usage() -> dict[str, Any]:
    return {
        "visitor_id": str(uuid.uuid4()),
        "analyses": 0,
        "resume_downloads": 0,
    }


def _normalize(raw: Any) -> dict[str, Any]:
    data = _default_usage()
    if isinstance(raw, dict):
        if raw.get("visitor_id"):
            data["visitor_id"] = str(raw["visitor_id"])
        try:
            data["analyses"] = max(0, int(raw.get("analyses", 0)))
        except (TypeError, ValueError):
            data["analyses"] = 0
        try:
            data["resume_downloads"] = max(0, int(raw.get("resume_downloads", 0)))
        except (TypeError, ValueError):
            data["resume_downloads"] = 0
    return data


def _merge_usage(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    left = _normalize(a)
    right = _normalize(b)
    return {
        "visitor_id": right.get("visitor_id") or left["visitor_id"],
        "analyses": max(left["analyses"], right["analyses"]),
        "resume_downloads": max(left["resume_downloads"], right["resume_downloads"]),
    }


def _call_store(
    write: dict[str, Any] | None = None, *, key: str = "ra_usage_read"
) -> dict[str, Any] | None:
    try:
        from usage_gate import usage_store

        value = usage_store(
            write=_normalize(write) if write is not None else None,
            key=key,
        )
        if isinstance(value, dict):
            return _normalize(value)
    except Exception:
        return None
    return None


def bootstrap_usage() -> dict[str, Any]:
    """Hydrate session usage from browser localStorage (falls back to session-only)."""
    if "usage" not in st.session_state:
        st.session_state.usage = _default_usage()

    pending_write = st.session_state.pop("_usage_write", None)
    stored = _call_store(
        _normalize(pending_write) if pending_write is not None else None,
        key="ra_usage_boot",
    )
    if stored is not None:
        base = pending_write if pending_write is not None else st.session_state.usage
        st.session_state.usage = _merge_usage(base, stored)
        st.session_state.usage_hydrated = True
    elif pending_write is not None:
        st.session_state.usage = _normalize(pending_write)
    return _normalize(st.session_state.usage)


def persist_usage(usage: dict[str, Any]) -> dict[str, Any]:
    """Update counters in session and queue a localStorage write for the next bootstrap."""
    usage = _normalize(usage)
    st.session_state.usage = usage
    st.session_state._usage_write = usage
    # Best-effort immediate write (separate component key from bootstrap).
    stored = _call_store(usage, key="ra_usage_write")
    if stored is not None:
        st.session_state.usage = _merge_usage(usage, stored)
    return _normalize(st.session_state.usage)


def analyses_left(usage: dict[str, Any] | None = None) -> int:
    usage = _normalize(usage or st.session_state.get("usage"))
    return max(0, max_analyses() - usage["analyses"])


def resume_downloads_left(usage: dict[str, Any] | None = None) -> int:
    usage = _normalize(usage or st.session_state.get("usage"))
    return max(0, max_resume_downloads() - usage["resume_downloads"])


def can_analyse(usage: dict[str, Any] | None = None) -> bool:
    return analyses_left(usage) > 0


def can_download_resume(usage: dict[str, Any] | None = None) -> bool:
    return resume_downloads_left(usage) > 0


def record_analysis() -> dict[str, Any]:
    usage = _normalize(st.session_state.get("usage"))
    usage["analyses"] += 1
    return persist_usage(usage)


def record_resume_download() -> dict[str, Any]:
    usage = _normalize(st.session_state.get("usage"))
    usage["resume_downloads"] += 1
    return persist_usage(usage)


def usage_banner_html(usage: dict[str, Any] | None = None) -> str:
    usage = _normalize(usage or st.session_state.get("usage"))
    a_left = analyses_left(usage)
    d_left = resume_downloads_left(usage)
    a_max = max_analyses()
    d_max = max_resume_downloads()
    return f"""
    <div class="usage-banner">
      <strong>Free explore limits</strong>
      <span>{a_left}/{a_max} analyse runs left</span>
      <span class="usage-dot">·</span>
      <span>{d_left}/{d_max} updated-resume downloads left</span>
    </div>
    """
