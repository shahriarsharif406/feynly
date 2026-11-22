"""Screen 3: fresh retest, then the proof that understanding changed (or honestly did not)."""
from __future__ import annotations

import re
from datetime import datetime, timezone

import streamlit as st

from core import config as C
from core.demo import match_demo_input
from core.i18n import num, t
from core.pipeline import run_grade
from core.scoring import after_score, build_proof_rows
from core.storage import get_conn, save_proof
from ui import components as ui
from ui.proof_card import build_proof_html, build_share_svg
from ui.reveal import render_reveal
from ui.state import reset_loop


def _fill_samples() -> None:
    s = st.session_state
    case = match_demo_input(s["inputs"])
    if not case:
        return
    for q in s["retest"].questions:
        v = case.sample_answers.get(q.q_id, "")
        s[f"ans_{q.q_id}"] = int(v) if q.type == "mcq" and str(v).isdigit() else v


def _loop_again() -> None:
    s = st.session_state
    inp = s["inputs"]
    reset_loop(keep_inputs=True)
    s["in_topic"], s["in_explanation"] = inp.topic or "", inp.explanation
    s["in_error"], s["in_code"] = inp.error_text or "", inp.code_snippet or ""
    s["mode"] = inp.mode
    s["notice"] = "rewrite_note"


def _new_loop() -> None:
    reset_loop(keep_inputs=False)


def render() -> None:
    s = st.session_state
    lang = s.get("output_lang") or s.get("lang") or "en"
    ui_lang = s.get("lang") or lang
    inp, analysis, retest = s["inputs"], s["analysis"], s["retest"]
    if inp is None or analysis is None or retest is None:
        reset_loop()
        st.rerun()
        return
    demo = C.is_demo_mode(s.get("force_demo", False))
    concepts = analysis.concepts

    if not s["retest_submitted"]:
        st.markdown(f'<div class="fy-h1" lang="{lang}">{t("h1_retest", ui_lang)}</div>', unsafe_allow_html=True)
        ui.banner("notice", t("retest_intro", ui_lang))
        by_id = {c.id: c for c in concepts}
        for q in retest.questions:
            c = by_id.get(q.concept_id)
            st.markdown(
                f'<div class="fy-card" lang="{lang}"><span class="fy-chip {c.status if c else "missing"}">'
                f'{ui.e(q.concept_id)} · {ui.e(c.label if c else "")}</span>'
                f'<div style="margin-top:8px;white-space:pre-wrap">{ui.e(q.prompt)}</div></div>',
                unsafe_allow_html=True,
            )
            if q.type == "mcq":
                st.radio(q.q_id, [0, 1, 2, 3], format_func=lambda i, q=q: q.options[i], index=None,
                         key=f"ans_{q.q_id}", label_visibility="collapsed")
            else:
                st.text_area(q.q_id, key=f"ans_{q.q_id}", height=100, max_chars=C.ANSWER_MAX,
                             placeholder=t("short_hint", ui_lang), label_visibility="collapsed")

        answered = all(
            (s.get(f"ans_{q.q_id}") is not None) if q.type == "mcq" else bool((s.get(f"ans_{q.q_id}") or "").strip())
            for q in retest.questions
        )
        _case = match_demo_input(inp)
        if _case and all(q.q_id in _case.sample_answers for q in retest.questions) and demo:
            st.button(t("btn_fill_samples", ui_lang), on_click=_fill_samples)
        if st.button(t("btn_submit", ui_lang), type="primary", disabled=not answered):
            answers = {q.q_id: str(s.get(f"ans_{q.q_id}")) for q in retest.questions}
            slot = st.empty()
            ui.loader(slot, "load_grade", ui_lang)
            grades = run_grade(inp, analysis, retest, answers, demo)
            slot.empty()
            rp = {q.concept_id: grades[q.q_id].points for q in retest.questions}
            s["answers"], s["grades"], s["retest_points"] = answers, grades, rp
            s["after_score"] = after_score(concepts, rp)
            s["retest_submitted"] = True
            st.rerun()
        return

    # ---------- Phase B: proof ----------
    before, after, rp = s["before_score"], s["after_score"], s["retest_points"]
    rows = build_proof_rows(concepts, retest, s["answers"], s["grades"])
    if not s["proof_saved"]:
        try:
            if s.get("attempt_id"):
                save_proof(get_conn(), s["attempt_id"], retest, s["answers"], s["grades"], rp, after)
        except Exception:
            pass
        s["proof_saved"] = True
    if s.get("notice"):
        ui.banner("notice", t(s["notice"], ui_lang))
        s["notice"] = None

    st.markdown(f'<div class="fy-h1" lang="{lang}">{t("h1_proof", ui_lang)}</div>', unsafe_allow_html=True)
    render_reveal(concepts, s["gaps"], rp, before, after, lang)
    st.markdown(f'<div class="fy-card" lang="{lang}">', unsafe_allow_html=True)
    ui.proof_strip(rows, lang)
    st.markdown("</div>", unsafe_allow_html=True)
    uncovered = sum(1 for c in concepts if c.id not in rp and c.status != "correct")
    if uncovered:
        st.caption(t("uncovered", ui_lang, n=num(uncovered, ui_lang)))
    st.caption(t("comparability", ui_lang))
    ui.disclaimer(ui_lang)

    slug = re.sub(r"[^a-z0-9]+", "-", analysis.topic_title.lower()).strip("-") or "proof"
    html_doc = build_proof_html(
        analysis.topic_title, lang, before, after, rows, datetime.now(timezone.utc).isoformat(), concepts, rp
    )
    share_txt = t("share_text", lang, topic=analysis.topic_title, before=num(before, lang), after=num(after, lang))
    with st.expander(t("share_title", ui_lang)):
        st.code(share_txt, language=None)
        st.download_button(t("btn_download_image", ui_lang),
                           build_share_svg(analysis.topic_title, lang, before, after, concepts, rp),
                           file_name=f"feynly-share-{slug}.svg", mime="image/svg+xml")
    b1, b2 = st.columns(2)
    b1.download_button(t("btn_download", ui_lang), html_doc, file_name=f"feynly-proof-{slug}.html",
                       mime="text/html", use_container_width=True)
    b2.button(t("btn_new_loop", ui_lang), type="primary", on_click=_new_loop, use_container_width=True)
    if any(r.still_gap for r in rows):
        st.button(t("btn_loop_again", ui_lang), on_click=_loop_again)
