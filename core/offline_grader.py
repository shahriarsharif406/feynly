"""Keyword grading used in Demo Mode for custom answers, and as the fallback when the AI is down."""
from __future__ import annotations

from .models import QuestionGrade, RetestQuestion
from .validation import normalize

_NOTE = {
    "en": "Graded offline by keyword match: found {found}.",
    "bn": "কিওয়ার্ড মিলিয়ে অফলাইনে মূল্যায়ন: পাওয়া গেছে {found}।",
}
_NONE = {"en": "no key ideas", "bn": "কোনো মূল ধারণা নয়"}


def grade_mcq(question: RetestQuestion, answer: str) -> QuestionGrade:
    try:
        ok = int(answer) == question.correct_option_index
    except (TypeError, ValueError):
        ok = False
    return QuestionGrade(q_id=question.q_id, points=2 if ok else 0, feedback="", graded_by="local_mcq")


def grade_short(question: RetestQuestion, answer: str, lang: str = "en") -> QuestionGrade:
    ans = normalize(answer)
    if not ans:
        return QuestionGrade(q_id=question.q_id, points=0, feedback="", graded_by="offline")
    hits = [t for t in dict.fromkeys(normalize(t) for t in question.rubric.key_terms) if t and t in ans]
    pts = 2 if len(hits) >= 2 else 1 if len(hits) == 1 else 0
    found = ", ".join(hits) if hits else _NONE.get(lang, _NONE["en"])
    return QuestionGrade(
        q_id=question.q_id,
        points=pts,
        feedback=_NOTE.get(lang, _NOTE["en"]).format(found=found),
        matched_ideas=hits,
        graded_by="offline",
    )
