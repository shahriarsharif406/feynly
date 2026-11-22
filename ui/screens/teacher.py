"""Teacher view: aggregate results for a shared class code. No student names are ever stored."""
from __future__ import annotations

import streamlit as st

from core.i18n import num, t
from core.storage import class_summary, get_conn


def render(lang: str) -> None:
    with st.expander(t("teacher_title", lang)):
        st.caption(t("teacher_privacy", lang))
        code = st.text_input(t("teacher_code", lang), key="teacher_code", max_chars=20)
        if not code.strip():
            return
        try:
            sm = class_summary(get_conn(), code)
        except Exception:
            sm = {"attempts": 0}
        if not sm["attempts"]:
            st.caption(t("teacher_none", lang))
            return
        b = "–" if sm["avg_before"] is None else num(sm["avg_before"], lang)
        a = "–" if sm["avg_after"] is None else num(sm["avg_after"], lang)
        st.write(t("teacher_stats", lang, n=num(sm["attempts"], lang), done=num(sm["finished"], lang), b=b, a=a))
        if sm["top_gaps"]:
            st.markdown(f"**{t('teacher_top', lang)}**")
            for g in sm["top_gaps"]:
                st.write(f"• {g['topic']} · {g['label']} ×{num(g['n'], lang)}")
