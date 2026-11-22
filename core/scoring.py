"""Scoring is pure Python. The AI labels checkpoints; code turns labels into numbers."""
from __future__ import annotations

import math
from typing import Optional

from .config import MAX_GAPS
from .models import Concept, GapRef, ProofRow, QuestionGrade, RetestSet, ScoreBreakdown, Status

POINTS: dict[str, int] = {"correct": 2, "partial": 1, "missing": 0, "misconception": 0}
_SEVERITY = {"misconception": 0, "missing": 1, "partial": 2}
_CONF = {"low": 0, "medium": 1, "high": 2}


def round_half_up(x: float) -> int:
    return int(math.floor(x + 0.5))


def points_for(status: str) -> int:
    return POINTS[status]


def status_from_points(points: int) -> Status:
    return {2: "correct", 1: "partial"}.get(points, "missing")  # type: ignore[return-value]


def _score(points: list[int]) -> int:
    n = len(points)
    return round_half_up(100 * sum(points) / (2 * n)) if n else 0


def before_score(concepts: list[Concept]) -> int:
    return _score([points_for(c.status) for c in concepts])


def select_gaps(concepts: list[Concept], max_gaps: int = MAX_GAPS) -> list[GapRef]:
    cands = [(i, c) for i, c in enumerate(concepts) if points_for(c.status) < 2]
    cands.sort(key=lambda ic: (_SEVERITY[ic[1].status], ic[0]))
    return [
        GapRef(gap_id=f"G{k + 1}", concept_id=c.id, kind=c.status)
        for k, (_, c) in enumerate(cands[:max_gaps])
    ]


def retest_targets(concepts: list[Concept], gaps: list[GapRef]) -> list[str]:
    if gaps:
        return [g.concept_id for g in gaps]
    order = sorted(range(len(concepts)), key=lambda i: (_CONF[concepts[i].confidence], i))
    return [concepts[i].id for i in order[:2]]


def after_score(concepts: list[Concept], retest_points: dict[str, int]) -> int:
    return _score([retest_points.get(c.id, points_for(c.status)) for c in concepts])


def breakdown(concepts: list[Concept], retest_points: Optional[dict[str, int]] = None) -> ScoreBreakdown:
    rp = retest_points or {}
    rows, total = [], 0
    for c in concepts:
        pts = rp.get(c.id, points_for(c.status))
        status = status_from_points(rp[c.id]) if c.id in rp else c.status
        rows.append((c.id, c.label, status, pts))
        total += pts
    score = _score([r[3] for r in rows])
    return ScoreBreakdown(rows=rows, total_points=total, max_points=2 * len(concepts), score=score)


def band(score: int) -> str:
    if score < 40:
        return "cracked"
    if score < 70:
        return "shaping"
    if score < 90:
        return "mended"
    return "golden"


def build_proof_rows(
    concepts: list[Concept],
    retest: RetestSet,
    answers: dict[str, str],
    grades: dict[str, QuestionGrade],
) -> list[ProofRow]:
    by_concept = {q.concept_id: q for q in retest.questions}
    rows: list[ProofRow] = []
    for c in concepts:
        q = by_concept.get(c.id)
        if q is None:
            continue
        g = grades.get(q.q_id)
        pts = g.points if g else 0
        ans = answers.get(q.q_id, "")
        if q.type == "mcq":
            try:
                ans = q.options[int(ans)]
            except (ValueError, IndexError):
                pass
        rows.append(
            ProofRow(
                concept_id=c.id,
                label=c.label,
                before_status=c.status,
                before_quote=c.evidence_quote,
                after_points=pts,
                after_status=status_from_points(pts),
                answer_snippet=(ans or "")[:120],
                feedback=g.feedback if g else "",
                still_gap=pts < 2,
            )
        )
    return rows
