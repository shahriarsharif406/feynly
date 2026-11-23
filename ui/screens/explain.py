"""Screen 1: the student explains a topic (or a bug) in their own words."""
from __future__ import annotations

import streamlit as st

from core import config as C
from core.demo import demo_for, demo_ids_for, load_demo, match_demo_input
from core.i18n import num, t
from core.models import LoopInput
from core.pipeline import StepFailed, run_analyze, run_lesson, run_transcribe
from core.storage import get_conn, progress_summary, save_attempt
from core.validation import validate_input
from ui import components as ui
from ui.bowl import hero_bowl
from ui.state import go


def _use_sample() -> None:
    s = st.session_state
    case = demo_for(s.get("mode") or "concept", s.get("lang") or "en", s.get("sample_pick"))
    s["in_topic"] = case.input.topic or ""
    s["in_explanation"] = case.input.explanation
    s["in_error"] = case.input.error_text or ""
    s["in_code"] = case.input.code_snippet or ""
    s["run_sample"] = True


def _use_transcript() -> None:
    s = st.session_state
    cap = C.EXPLANATION_MAX_CONCEPT if (s.get("mode") or "concept") == "concept" else C.EXPLANATION_MAX_CODE
    s["in_explanation"] = f'{s.get("in_explanation") or ""} {s.get("voice_text") or ""}'.strip()[:cap]
    s["voice_text"] = None


def _voice(lang: str, demo: bool) -> None:
    """Optional: speak the explanation. Gemini transcribes it; the student reviews it before use."""
    s = st.session_state
    if demo or not hasattr(st, "audio_input"):
        if demo:
            st.caption(t("voice_demo", lang))
        return
    audio = st.audio_input(t("voice_label", lang), key="voice_audio")
    if audio is not None:
        data = audio.getvalue()
        h = hash(data)
        if h != s.get("voice_hash"):
            s["voice_hash"] = h
            try:
                with st.spinner(t("voice_transcribing", lang)):
                    s["voice_text"] = run_transcribe(data, audio.type or "audio/wav", lang)
            except StepFailed:
                s["voice_text"] = None
                st.caption(":red[" + t("voice_fail", lang) + "]")
    if s.get("voice_text"):
        st.text_area(t("voice_label", lang), value=s["voice_text"], key="voice_text", height=90, label_visibility="collapsed")
        st.button(t("voice_use", lang), on_click=_use_transcript)


def _collect(mode: str, lang: str) -> LoopInput:
    s = st.session_state
    return LoopInput(
        mode=mode,  # type: ignore[arg-type]
        topic=(s.get("in_topic") or "").strip() or None if mode == "concept" else None,
        explanation=(s.get("in_explanation") or "").strip(),
        error_text=(s.get("in_error") or "").strip() or None if mode == "code" else None,
        code_snippet=(s.get("in_code") or "").strip() or None if mode == "code" else None,
        output_lang=lang,  # type: ignore[arg-type]
    )


def _run(inp: LoopInput, demo: bool, lang: str) -> None:
    s = st.session_state
    slot = st.empty()
    try:
        ui.loader(slot, "load_reading", lang)
        # analysis and lesson are two AI steps; the loader text walks through the story
        analysis, gaps, targets, before, source = run_analyze(inp, demo)
        if not analysis.input_ok:
            slot.empty()
            s["error_key"] = f"issue_{analysis.input_issue}"
            st.rerun()
            return
        ui.loader(slot, "load_gaps", lang)
        lesson = run_lesson(inp, analysis, gaps, demo)
        ui.loader(slot, "load_lesson", lang)
    except StepFailed as ex:
        slot.empty()
        s["error_key"] = ex.key
        st.rerun()
        return
    slot.empty()
    case = match_demo_input(inp) if demo else None
    s["inputs"], s["output_lang"] = inp, lang
    s["analysis"], s["gaps"], s["retest_targets"], s["lesson"] = analysis, gaps, targets, lesson
    s["before_score"], s["source"] = before, source
    s["demo_id"] = case.demo_id if case else None
    try:
        s["attempt_id"] = save_attempt(
            get_conn(), s["session_id"], inp, analysis, gaps, lesson, before, source, s["demo_id"], s.get("last_model"),
            (s.get("in_class") or "").strip().upper() or None,
        )
    except Exception:
        s["attempt_id"] = None  # history is a convenience; never block the loop on storage
    s["error_key"] = None
    go("gaps")


def render() -> None:
    s = st.session_state
    lang = s.get("lang") or "en"
    demo = C.is_demo_mode(s.get("force_demo", False))
    mode = s.get("mode") or "concept"

    st.markdown(
        f'<div class="fy-hero"><div class="fy-h1" lang="{lang}">{t("h1_explain", lang)}</div>'
        f'<div class="fy-orb" aria-hidden="true">{hero_bowl(190)}</div></div>',
        unsafe_allow_html=True,
    )
    st.segmented_control(
        t("mode_label", lang),
        ["concept", "code"],
        format_func=lambda m: t("mode_concept", lang) if m == "concept" else t("mode_code", lang),
        key="mode",
        label_visibility="collapsed",
    )
    mode = s.get("mode") or "concept"

    if demo:
        ui.banner("demo", t("banner_demo", lang))
    if s.get("notice"):
        ui.banner("notice", t(s["notice"], lang))
        s["notice"] = None

    ids = demo_ids_for(mode, lang)
    if len(ids) > 1:
        st.selectbox(t("sample_pick", lang), ids, key="sample_pick",
                     format_func=lambda i: load_demo(i).topic or i)

    _voice(lang, demo)

    if mode == "concept":
        st.text_input(t("topic_label", lang), key="in_topic", max_chars=C.TOPIC_MAX, placeholder=t("topic_ph", lang))
        st.text_area(t("explain_label", lang), key="in_explanation", height=220, max_chars=C.EXPLANATION_MAX_CONCEPT,
                     placeholder=t("explain_ph", lang))
    else:
        st.markdown('<div class="fy-mono">', unsafe_allow_html=True)
        st.text_area(t("error_label", lang), key="in_error", height=130, max_chars=C.ERROR_MAX, placeholder=t("error_ph", lang))
        st.text_area(t("code_label", lang), key="in_code", height=110, max_chars=C.CODE_MAX)
        st.markdown("</div>", unsafe_allow_html=True)
        st.text_area(t("why_label", lang), key="in_explanation", height=130, max_chars=C.EXPLANATION_MAX_CODE)

    st.text_input(t("class_label", lang), key="in_class", max_chars=20, placeholder=t("class_ph", lang))

    exp_len = len(s.get("in_explanation") or "")
    cap = C.EXPLANATION_MAX_CONCEPT if mode == "concept" else C.EXPLANATION_MAX_CODE
    st.caption(f"{exp_len} / {cap}")

    inp = _collect(mode, lang)
    errs = validate_input(inp)
    if errs and (s.get("in_explanation") or s.get("in_error")):
        st.caption(":red[" + " · ".join(t(k, lang) for k in errs) + "]")
    elif not s.get("in_explanation"):
        st.caption(t("hint_min", lang, n=C.EXPLANATION_MIN_CONCEPT if mode == "concept" else C.EXPLANATION_MIN_CODE))

    c1, c2 = st.columns([3, 2])
    go_click = c1.button(t("btn_check", lang), type="primary", disabled=bool(errs), use_container_width=True)
    c2.button(t("btn_sample", lang), on_click=_use_sample, use_container_width=True)

    if s.get("error_key"):
        key = s["error_key"]
        ui.banner("error", t(key, lang))
        if key == "err_ai_busy" and s.get("last_ai_error"):
            st.caption(f"Details: {s['last_ai_error']}")
        if key in ("err_ai_busy", "err_budget") and st.button(t("btn_run_demo", lang)):
            s["force_demo"] = True
            _use_sample()
            s["error_key"] = None
            st.rerun()

    if s.pop("run_sample", False):
        sample_inp = _collect(mode, lang)
        if not validate_input(sample_inp):
            _run(sample_inp, demo, lang)
            return
    if go_click and not errs:
        _run(inp, demo, lang)
        return

    try:
        prog = progress_summary(get_conn(), s["session_id"])
    except Exception:
        prog = {"loops": [], "open_gaps": []}
    with st.expander(t("progress_title", lang)):
        if not prog["loops"]:
            st.caption(t("progress_empty", lang))
        for r in prog["loops"]:
            st.write(f"{r['topic_title']} · {num(r['before_score'], lang)} → {num(r['after_score'], lang)} · {r['created_at'][:10]}")
        if prog["open_gaps"]:
            st.markdown(f"**{t('recurring_gaps', lang)}**")
            for g in prog["open_gaps"]:
                st.write(f"• {g['label']} ×{num(g['n'], lang)}")
