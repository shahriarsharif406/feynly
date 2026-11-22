"""Feynly: Explain it. Fix it. Prove it."""
from __future__ import annotations

import streamlit as st

from core import config as C
from core.i18n import t
from ui import components as ui
from ui import state, theme
from ui.screens import explain, gaps, proof


@st.dialog("How scoring works")
def _scoring_dialog(lang: str) -> None:
    st.write(t("scoring_explainer", lang))


def main() -> None:
    st.set_page_config(page_title="Feynly", page_icon="🏺", layout="centered", initial_sidebar_state="collapsed")
    theme.inject()
    state.init()
    s = st.session_state

    _, tog = st.columns([3, 1])
    with tog:
        st.segmented_control("lang", ["en", "bn"], format_func=lambda x: "EN" if x == "en" else "বাং",
                             key="lang", label_visibility="collapsed")
    lang = s.get("lang") or "en"
    demo = C.is_demo_mode(s.get("force_demo", False))

    ui.top_bar(lang, demo)
    ui.stepper(s["stage"], lang)

    {"explain": explain.render, "gaps": gaps.render, "proof": proof.render}[s["stage"]]()

    ui.footer(lang)
    f1, f2 = st.columns([2, 2])
    with f1:
        if st.button(t("how_score_works", lang), key="open_scoring"):
            _scoring_dialog(lang)
    with f2:
        st.toggle(t("force_demo", lang), key="force_demo", disabled=C.get_api_key() is None)


main()
