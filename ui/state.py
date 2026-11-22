"""All session-state keys live here. Only this module writes defaults."""
from __future__ import annotations

import uuid

import streamlit as st

LOOP_KEYS = [
    "analysis", "gaps", "retest_targets", "lesson", "retest", "answers", "grades",
    "retest_submitted", "proof_saved", "before_score", "after_score", "attempt_id",
    "demo_id", "source", "retest_points",
]


def init() -> None:
    s = st.session_state
    s.setdefault("session_id", uuid.uuid4().hex)
    s.setdefault("lang", "en")
    s.setdefault("output_lang", "en")
    s.setdefault("stage", "explain")
    s.setdefault("mode", "concept")
    s.setdefault("force_demo", False)
    s.setdefault("inputs", None)
    s.setdefault("ai_calls_used", 0)
    s.setdefault("last_call_ts", 0.0)
    s.setdefault("notice", None)
    s.setdefault("error_key", None)
    s.setdefault("run_sample", False)
    _reset_downstream()


def _reset_downstream(force: bool = False) -> None:
    s = st.session_state
    defaults = {
        "analysis": None, "gaps": [], "retest_targets": [], "lesson": None, "retest": None,
        "answers": {}, "grades": {}, "retest_submitted": False, "proof_saved": False,
        "before_score": None, "after_score": None, "attempt_id": None, "demo_id": None,
        "source": None, "retest_points": {},
    }
    for k, v in defaults.items():
        if force or k not in s:
            s[k] = v


def reset_loop(keep_inputs: bool = False) -> None:
    s = st.session_state
    _reset_downstream(force=True)
    for k in [k for k in s.keys() if k.startswith("ans_")]:
        del s[k]
    if not keep_inputs:
        s["inputs"] = None
        for k in ("in_topic", "in_explanation", "in_error", "in_code"):
            s[k] = ""
    s["stage"] = "explain"
    s["notice"] = None
    s["error_key"] = None


def go(stage: str) -> None:
    st.session_state["stage"] = stage
    st.rerun()
