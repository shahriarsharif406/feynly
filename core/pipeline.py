"""The only module that decides live vs demo. The UI calls these functions and nothing else."""
from __future__ import annotations

import hashlib
import time

from . import config as C
from .ai_client import AIUnavailable, get_client
from .demo import match_demo_input
from .models import (
    AnalyzeResult,
    GapRef,
    GradeResult,
    LessonResult,
    LoopInput,
    QuestionGrade,
    RetestSet,
)
from .offline_grader import grade_mcq, grade_short
from .prompts import build_analyze_prompt, build_grade_prompt, build_lesson_prompt, build_retest_prompt
from .scoring import before_score, retest_targets, select_gaps
from .validation import (
    normalize,
    validate_analysis,
    validate_grades,
    validate_lesson,
    validate_retest,
)

DEMO_STEP_DELAY = 0.6
_CACHE: dict[str, object] = {}
_local_state: dict = {}


class StepFailed(Exception):
    """Carries an i18n key explaining what the UI should show."""

    def __init__(self, key: str) -> None:
        super().__init__(key)
        self.key = key


def _state():
    try:
        import streamlit as st

        return st.session_state
    except Exception:  # pragma: no cover
        return _local_state


def _get_client():
    return get_client()


def can_call_ai() -> bool:
    return int(_state().get("ai_calls_used", 0)) < C.MAX_AI_CALLS_PER_SESSION


def record_ai_call() -> None:
    s = _state()
    s["ai_calls_used"] = int(s.get("ai_calls_used", 0)) + 1
    s["last_call_ts"] = time.time()


def _throttle() -> None:
    last = float(_state().get("last_call_ts", 0.0))
    wait = C.MIN_SECONDS_BETWEEN_CALLS - (time.time() - last)
    if wait > 0:
        time.sleep(wait)


def _live(name, system, user, schema, temperature, max_tokens, validator, lang):
    client = _get_client()
    if client is None:
        raise StepFailed("err_no_key")
    key = hashlib.sha256(f"{name}|{client.primary}|{lang}|{system}|{user}".encode()).hexdigest()
    if key in _CACHE:
        return _CACHE[key].model_copy(deep=True)  # type: ignore[attr-defined]
    if not can_call_ai():
        raise StepFailed("err_budget")
    _throttle()
    record_ai_call()
    try:
        res, model = client.generate_json(system, user, schema, temperature, max_tokens, validator)
    except Exception as e:  # match by name: Streamlit can reload ai_client and change the class identity
        if not isinstance(e, AIUnavailable) and type(e).__name__ != "AIUnavailable":
            raise
        _state()["last_ai_error"] = getattr(client, "last_error", "")
        raise StepFailed("err_ai_busy")
    _state()["last_model"] = model
    _CACHE[key] = res
    return res.model_copy(deep=True)


def _sim(demo: bool) -> None:
    if demo:
        time.sleep(DEMO_STEP_DELAY)


def run_analyze(inp: LoopInput, demo: bool) -> tuple[AnalyzeResult, list[GapRef], list[str], int, str]:
    if demo:
        case = match_demo_input(inp)
        if case is None:
            raise StepFailed("err_demo_custom")
        _sim(True)
        analysis = case.analysis
        source = "demo"
    else:
        system, user = build_analyze_prompt(inp)
        analysis = _live(
            "analyze", system, user, AnalyzeResult, 0.2, 2048,
            lambda r: validate_analysis(r, inp.explanation), inp.output_lang,
        )
        source = "live"
    if not analysis.input_ok:
        return analysis, [], [], 0, source
    gaps = select_gaps(analysis.concepts)
    targets = retest_targets(analysis.concepts, gaps)
    return analysis, gaps, targets, before_score(analysis.concepts), source


def run_lesson(inp: LoopInput, analysis: AnalyzeResult, gaps: list[GapRef], demo: bool) -> LessonResult | None:
    if not gaps:
        return None
    if demo:
        case = match_demo_input(inp)
        if case is None:
            raise StepFailed("err_demo_custom")
        _sim(True)
        return case.lesson
    system, user = build_lesson_prompt(inp, analysis, gaps)
    return _live(
        "lesson", system, user, LessonResult, 0.5, 2048,
        lambda r: validate_lesson(r, gaps, inp.mode), inp.output_lang,
    )


def run_retest_generate(
    inp: LoopInput, analysis: AnalyzeResult, targets: list[str], lesson: LessonResult | None, demo: bool
) -> RetestSet:
    if demo:
        case = match_demo_input(inp)
        if case is None:
            raise StepFailed("err_demo_custom")
        _sim(True)
        return case.retest
    system, user = build_retest_prompt(inp, analysis, targets, lesson)
    return _live(
        "retest", system, user, RetestSet, 0.6, 1536,
        lambda r: validate_retest(r, targets, lesson), inp.output_lang,
    )


def run_grade(
    inp: LoopInput,
    analysis: AnalyzeResult,
    retest: RetestSet,
    answers: dict[str, str],
    demo: bool,
) -> dict[str, QuestionGrade]:
    grades: dict[str, QuestionGrade] = {}
    pending = []  # short, non-blank answers
    case = match_demo_input(inp) if demo else None
    for q in retest.questions:
        ans = answers.get(q.q_id, "")
        if q.type == "mcq":
            grades[q.q_id] = grade_mcq(q, ans)
        elif not (ans or "").strip():
            grades[q.q_id] = QuestionGrade(q_id=q.q_id, points=0, graded_by="offline")
        elif case and q.q_id in case.grades and normalize(ans) == normalize(case.sample_answers.get(q.q_id, "")):
            g = case.grades[q.q_id]
            grades[q.q_id] = QuestionGrade(**g.model_dump(), graded_by="demo")
        else:
            pending.append((q, ans))
    if not pending:
        return grades
    if not demo:
        try:
            system, user = build_grade_prompt(analysis.topic_title, inp.output_lang, pending)
            ids = {q.q_id for q, _ in pending}
            res = _live(
                "grade", system, user, GradeResult, 0.0, 1024,
                lambda r: validate_grades(r, ids), inp.output_lang,
            )
            for g in res.grades:  # type: ignore[attr-defined]
                grades[g.q_id] = QuestionGrade(**g.model_dump(), graded_by="ai")
            return grades
        except StepFailed:
            pass  # fall through to offline grading
    for q, ans in pending:
        grades[q.q_id] = grade_short(q, ans, inp.output_lang)
    _state()["notice"] = "graded_offline"
    return grades


def run_transcribe(audio: bytes, mime: str, lang: str) -> str:
    """Optional voice input (Live AI only). Counts against the session AI budget."""
    client = _get_client()
    if client is None:
        raise StepFailed("err_no_key")
    if not can_call_ai():
        raise StepFailed("err_budget")
    _throttle()
    record_ai_call()
    try:
        return client.transcribe(audio, mime, lang)
    except Exception as e:
        if not isinstance(e, AIUnavailable) and type(e).__name__ != "AIUnavailable":
            raise
        raise StepFailed("err_ai_busy")
