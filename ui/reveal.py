"""The before/after reveal: gold seams draw, the score counts up. Self-contained HTML, no external JS."""
from __future__ import annotations

import html
import json
from pathlib import Path

import streamlit.components.v1 as components

from core.i18n import band_label, num, t
from core.models import Concept, GapRef
from core.scoring import band
from ui.bowl import segment_data

TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "reveal_template.html"


def build_reveal_html(
    concepts: list[Concept], retest_points: dict[str, int], before: int, after: int, lang: str
) -> str:
    delta = after - before
    sign = "+" if delta >= 0 else "−"
    delta_txt = f"{sign}{num(abs(delta), lang)}"
    if delta < 0:
        delta_txt += " · " + t("reveal_negative", lang)
    caption = t("reveal_caption", lang, before=num(before, lang), after=num(after, lang), n=num(len(concepts), lang))
    repl = {
        "{{SEGMENTS_JSON}}": json.dumps(segment_data(concepts, retest_points)),
        "{{BEFORE}}": str(int(before)),
        "{{AFTER}}": str(int(after)),
        "{{BEFORE_TXT}}": num(before, lang),
        "{{BAND_BEFORE}}": html.escape(band_label(band(before), lang)),
        "{{BAND_AFTER_JSON}}": json.dumps(band_label(band(after), lang)),
        "{{DELTA}}": html.escape(delta_txt),
        "{{DELTA_JSON}}": json.dumps(delta_txt),
        "{{CAPTION}}": html.escape(caption),
        "{{LANG}}": "bn" if lang == "bn" else "en",
        "{{IS_BN}}": "true" if lang == "bn" else "false",
    }
    out = TEMPLATE.read_text(encoding="utf-8")
    for k, v in repl.items():
        out = out.replace(k, v)
    return out


def render_reveal(
    concepts: list[Concept],
    gaps: list[GapRef],
    retest_points: dict[str, int],
    before: int,
    after: int,
    lang: str,
) -> None:
    components.html(build_reveal_html(concepts, retest_points, before, after, lang), height=370)
