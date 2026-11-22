"""Central configuration. Change model names here if Google renames free-tier models."""
from __future__ import annotations

import os

MODEL_PRIMARY = os.environ.get("FEYNLY_MODEL", "gemini-3.8-flash")
MODEL_FALLBACK = os.environ.get("FEYNLY_MODEL_FALLBACK", "gemini-3.5-flash-lite")
DB_PATH = os.environ.get("FEYNLY_DB", "./data/feynly.db")
PROMPT_VERSION = "v1"

MAX_AI_CALLS_PER_SESSION = 12
MIN_SECONDS_BETWEEN_CALLS = 4.0
MAX_GAPS = 3
REQUEST_TIMEOUT_S = 30

EXPLANATION_MIN_CONCEPT = 40
EXPLANATION_MAX_CONCEPT = 1500
EXPLANATION_MIN_CODE = 20
EXPLANATION_MAX_CODE = 1000
ERROR_MIN = 10
ERROR_MAX = 3000
CODE_MAX = 2000
TOPIC_MAX = 80
ANSWER_MAX = 400


def get_api_key() -> str | None:
    """Key from Streamlit secrets, falling back to the environment. Never logged."""
    try:
        import streamlit as st

        key = st.secrets.get("GEMINI_API_KEY")  # type: ignore[attr-defined]
        if key and str(key).strip() and "your-key" not in str(key):
            return str(key).strip()
    except Exception:
        pass
    key = os.environ.get("GEMINI_API_KEY")
    if key and key.strip() and "your-key" not in key:
        return key.strip()
    return None


def is_demo_mode(force_demo: bool = False) -> bool:
    return bool(force_demo) or get_api_key() is None
