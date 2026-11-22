"""Screen 2: possible gaps (fracture cards) and the short mend lessons."""
from __future__ import annotations

import streamlit as st

from core import config as C
from core.i18n import band_label, num, t
from core.pipeline import StepFailed, run_retest_generate
from core.scoring import band, breakdown
from ui import components as ui
from ui.bowl import bowl_svg
from ui.state import go, reset_loop


def _edit_back() -> None:
    s = st.session_state
    inp = s["inputs"]
    reset_loop(keep_inputs=True)
    s["in_topic"], s["in_explanation"] = inp.topic or "", inp.explanation
    s["in_error"], s["in_code"] = inp.error_text or "", inp.code_snippet or ""
    s["mode"] = inp.mode


def render() -> None:
    s = st.session_state
    lang = s["output_lang"] if s.get("output_lang") else (s.get("lang") or "en")
    ui_lang = s.get("lang") or lang
    analysis, gaps, lesson = s["analysis"], s["gaps"], s["lesson"]
    inp = s["inputs"]
    if analysis is None or inp is None:
        reset_loop()
        go("explain")
        return
    demo = C.is_demo_mode(s.get("force_demo", False))
    before = s["before_score"]
    concepts = analysis.concepts
    if ui_lang != lang:
        st.caption(t("lang_note", ui_lang))

    c1, c2 = st.columns([1, 2])
    with c1:
        svg = bowl_svg(concepts, None, before, size=210, band_text=band_label(band(before), lang), score_text=num(before, lang))
        st.markdown(f'<div style="text-align:center">{svg}</div>', unsafe_allow_html=True)
    with c2:
        st.markdown(
            f'<div class="fy-headline" lang="{lang}">{ui.e(analysis.topic_title)}</div>'
            f'<div lang="{lang}">{ui.e(analysis.praise)}</div>'
            f'<div class="fy-muted" style="margin-top:6px">{ui.e(t("gaps_found", lang, n=num(len(gaps), lang)))}</div>',
            unsafe_allow_html=True,
        )
        with st.expander(t("how_score_works", lang)):
            ui.breakdown_table(breakdown(concepts), lang)

    ui.concept_chips(concepts, gaps, lang)
    ui.disclaimer(lang)

    by_id = {c.id: c for c in concepts}
    if not gaps:
        ui.banner("notice", t("no_gaps", lang))
    lessons = {l.gap_id: l for l in (lesson.lessons if lesson else [])}
    for g in gaps:
        ui.fracture_card(by_id[g.concept_id], g, lang)
        if g.gap_id in lessons:
            ui.mend_card(lessons[g.gap_id], lang)

    if s.get("error_key"):
        ui.banner("error", t(s["error_key"], ui_lang))

    b1, b2 = st.columns([3, 2])
    ready = b1.button(t("btn_ready", ui_lang), type="primary", use_container_width=True)
    b2.button(t("btn_edit", ui_lang), on_click=_edit_back, use_container_width=True)

    if ready:
        slot = st.empty()
        ui.loader(slot, "load_retest", ui_lang)
        try:
            s["retest"] = run_retest_generate(inp, analysis, s["retest_targets"], lesson, demo)
        except StepFailed as ex:
            slot.empty()
            s["error_key"] = ex.key
            st.rerun()
            return
        slot.empty()
        s["error_key"] = None
        s["answers"], s["grades"], s["retest_submitted"] = {}, {}, False
        go("proof")
