"""Injects the Feynly visual identity: terracotta, gold seams, handmade paper."""
from __future__ import annotations

from pathlib import Path

import streamlit as st

ASSETS = Path(__file__).resolve().parent.parent / "assets"
FONTS = (
    "https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&"
    "family=Hind+Siliguri:wght@400;500;600&family=Tiro+Bangla&family=JetBrains+Mono:wght@400&display=swap"
)


def css_text() -> str:
    return (ASSETS / "styles.css").read_text(encoding="utf-8")


def inject() -> None:
    st.markdown(f"<style>@import url('{FONTS}');\n{css_text()}</style>", unsafe_allow_html=True)
