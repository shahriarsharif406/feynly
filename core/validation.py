"""Input checks and consistency repair for AI output. Bad output is repaired or retried, never trusted."""
from __future__ import annotations

import difflib
import re
import unicodedata

from . import config as C
from .models import (
    AnalyzeResult,
    GapRef,
    GradeResult,
    LessonResult,
    LoopInput,
    RetestQuestion,
    RetestSet,
)


class ConsistencyError(ValueError):
    pass


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text.casefold()


def trim_words(text: str, max_words: int) -> str:
    words = (text or "").split()
    if len(words) <= max_words:
        return (text or "").strip()
    return " ".join(words[:max_words]).rstrip(".,;:") + "…"


_ERR_RE = re.compile(
    r"error|exception|traceback|line \d+|undefined|cannot|can't|failed|warning|not defined|null|nan", re.I
)


def looks_like_error(text: str) -> bool:
    return bool(_ERR_RE.search(text or ""))


def validate_input(inp: LoopInput) -> list[str]:
    """Returns i18n error keys. Empty list means the input is fine."""
    errs: list[str] = []
    exp = (inp.explanation or "").strip()
    if inp.mode == "concept":
        if not (inp.topic or "").strip():
            errs.append("err_topic_missing")
        elif len(inp.topic or "") > C.TOPIC_MAX:
            errs.append("err_topic_long")
        if len(exp) < C.EXPLANATION_MIN_CONCEPT:
            errs.append("err_too_short")
        elif len(exp) > C.EXPLANATION_MAX_CONCEPT:
            errs.append("err_too_long")
    else:
        err = (inp.error_text or "").strip()
        if len(err) < C.ERROR_MIN:
            errs.append("err_error_short")
        elif len(err) > C.ERROR_MAX:
            errs.append("err_error_long")
        elif not looks_like_error(err):
            errs.append("err_not_error")
        if len(inp.code_snippet or "") > C.CODE_MAX:
            errs.append("err_code_long")
        if len(exp) < C.EXPLANATION_MIN_CODE:
            errs.append("err_too_short")
        elif len(exp) > C.EXPLANATION_MAX_CODE:
            errs.append("err_too_long")
    return errs


def validate_analysis(res: AnalyzeResult, explanation: str) -> AnalyzeResult:
    if not res.input_ok:
        if res.input_issue is None:
            raise ConsistencyError("input_ok=false requires input_issue")
        return res
    n = len(res.concepts)
    if n < 3 and n > 0:
        raise ConsistencyError(f"need 3-5 concepts, got {n}")
    if n == 0 or n > 5:
        raise ConsistencyError(f"need 3-5 concepts, got {n}")
    norm_exp = normalize(explanation)
    for i, c in enumerate(res.concepts, start=1):
        c.id = f"C{i}"
        c.label = trim_words(c.label, 8)
        c.expected_idea = trim_words(c.expected_idea, 30)
        c.reason = trim_words(c.reason, 30)
        c.gap_headline = trim_words(c.gap_headline, 10)
        q = (c.evidence_quote or "").strip()
        if q and normalize(q) not in norm_exp:
            q = ""
            c.confidence = "low"
        c.evidence_quote = q
        if c.status == "misconception" and not q:
            c.status = "missing"
        elif c.status == "correct" and not q:
            c.status = "partial"
            c.confidence = "low"
        if c.status != "correct" and not c.gap_headline:
            c.gap_headline = c.label
        if c.status == "correct":
            c.gap_headline = ""
    res.topic_title = trim_words(res.topic_title, 12)[:60]
    res.praise = trim_words(res.praise, 25)
    return res


def validate_lesson(res: LessonResult, gaps: list[GapRef], mode: str) -> LessonResult:
    if len(res.lessons) < len(gaps):
        raise ConsistencyError("missing lessons")
    out = []
    for gap, les in zip(gaps, res.lessons):
        les.gap_id, les.concept_id = gap.gap_id, gap.concept_id
        les.title = trim_words(les.title, 8)
        les.core_idea = trim_words(les.core_idea, 60)
        les.example = trim_words(les.example, 60)
        les.you_said = trim_words(les.you_said, 25)
        les.actually = trim_words(les.actually, 25)
        les.check_yourself = trim_words(les.check_yourself, 20)
        if mode == "concept":
            les.code_fix = None
        elif les.code_fix:
            les.code_fix.before = "\n".join(les.code_fix.before.splitlines()[:20])
            les.code_fix.after = "\n".join(les.code_fix.after.splitlines()[:20])
        out.append(les)
    res.lessons = out
    res.estimated_read_seconds = max(20, min(180, int(res.estimated_read_seconds or 60)))
    return res


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?।])\s+", text or "") if s.strip()]


def validate_retest(res: RetestSet, targets: list[str], lesson: LessonResult | None) -> RetestSet:
    if len(res.questions) != len(targets):
        raise ConsistencyError("one question per target required")
    lesson_sents: list[str] = []
    if lesson:
        for les in lesson.lessons:
            lesson_sents += _sentences(les.core_idea) + _sentences(les.example) + [les.check_yourself]
    out: list[RetestQuestion] = []
    for k, (q, tgt) in enumerate(zip(res.questions, targets), start=1):
        q.q_id, q.concept_id = f"Q{k}", tgt
        q.prompt = trim_words(q.prompt, 50) if q.type == "mcq" else trim_words(q.prompt, 60)
        if q.type == "mcq":
            opts = [o.strip() for o in q.options]
            if len(opts) != 4 or any(not o for o in opts) or len({o.casefold() for o in opts}) != 4:
                raise ConsistencyError("mcq needs 4 distinct options")
            if q.correct_option_index is None or not 0 <= q.correct_option_index <= 3:
                raise ConsistencyError("bad correct_option_index")
            q.options = opts
        else:
            q.options, q.correct_option_index = [], None
        terms = []
        for t in q.rubric.key_terms:
            t = t.strip().lower()
            if len(t) >= 2 and t not in terms:
                terms.append(t)
        if q.type == "short" and len(terms) < 2:
            raise ConsistencyError("need >=2 key terms")
        q.rubric.key_terms = terms
        q.rubric.full_credit = trim_words(q.rubric.full_credit, 30)
        q.rubric.partial_credit = trim_words(q.rubric.partial_credit, 30)
        for s in lesson_sents:
            if s and difflib.SequenceMatcher(None, normalize(q.prompt), normalize(s)).ratio() >= 0.8:
                raise ConsistencyError("question copies lesson text")
        out.append(q)
    if len(out) >= 2 and all(q.type == "mcq" for q in out):
        raise ConsistencyError("need at least one short question")
    res.questions = out
    return res


def validate_grades(res: GradeResult, expected_q_ids: set[str]) -> GradeResult:
    if {g.q_id for g in res.grades} != set(expected_q_ids):
        raise ConsistencyError("grade q_ids mismatch")
    for g in res.grades:
        g.points = max(0, min(2, int(g.points)))
        g.feedback = trim_words(g.feedback, 30)
        if g.points >= 1 and not g.matched_ideas:
            g.points = min(g.points, 1)
    return res
