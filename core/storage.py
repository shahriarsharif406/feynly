"""SQLite history. Convenience only: Streamlit Cloud storage is ephemeral."""
from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from . import config as C
from .models import AnalyzeResult, GapRef, LessonResult, LoopInput, QuestionGrade, RetestSet
from .scoring import points_for

SCHEMA = """
CREATE TABLE IF NOT EXISTS attempts (
  id TEXT PRIMARY KEY, created_at TEXT NOT NULL, session_id TEXT NOT NULL,
  mode TEXT NOT NULL CHECK (mode IN ('concept','code')),
  output_lang TEXT NOT NULL CHECK (output_lang IN ('en','bn')),
  source TEXT NOT NULL CHECK (source IN ('live','demo')),
  demo_id TEXT, topic_title TEXT NOT NULL, explanation TEXT NOT NULL,
  error_text TEXT, code_snippet TEXT, model TEXT, prompt_version TEXT NOT NULL,
  analysis_json TEXT NOT NULL, lesson_json TEXT,
  before_score INTEGER NOT NULL, after_score INTEGER, delta INTEGER
);
CREATE TABLE IF NOT EXISTS concept_results (
  attempt_id TEXT NOT NULL REFERENCES attempts(id), concept_id TEXT NOT NULL,
  label TEXT NOT NULL, before_status TEXT NOT NULL, before_points INTEGER NOT NULL,
  is_gap INTEGER NOT NULL, retested INTEGER NOT NULL DEFAULT 0, after_points INTEGER,
  PRIMARY KEY (attempt_id, concept_id)
);
CREATE TABLE IF NOT EXISTS retest_items (
  attempt_id TEXT NOT NULL REFERENCES attempts(id), q_id TEXT NOT NULL,
  concept_id TEXT NOT NULL, type TEXT NOT NULL CHECK (type IN ('mcq','short')),
  question_json TEXT NOT NULL, answer TEXT, points INTEGER, feedback TEXT,
  graded_by TEXT CHECK (graded_by IN ('local_mcq','ai','offline','demo')),
  PRIMARY KEY (attempt_id, q_id)
);
CREATE INDEX IF NOT EXISTS idx_attempts_session ON attempts(session_id, created_at);
"""


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def _connect(path: str) -> sqlite3.Connection:
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    return conn


def get_conn(path: str | None = None) -> sqlite3.Connection:
    path = path or C.DB_PATH
    try:
        import streamlit as st

        @st.cache_resource(show_spinner=False)
        def _cached(p: str) -> sqlite3.Connection:
            return _connect(p)

        return _cached(path)
    except Exception:
        return _connect(path)


def save_attempt(
    conn: sqlite3.Connection,
    session_id: str,
    inp: LoopInput,
    analysis: AnalyzeResult,
    gaps: list[GapRef],
    lesson: LessonResult | None,
    before: int,
    source: str,
    demo_id: str | None,
    model: str | None,
) -> str:
    aid = uuid.uuid4().hex
    conn.execute(
        "INSERT INTO attempts (id, created_at, session_id, mode, output_lang, source, demo_id, topic_title,"
        " explanation, error_text, code_snippet, model, prompt_version, analysis_json, lesson_json, before_score)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            aid, datetime.now(timezone.utc).isoformat(), session_id, inp.mode, inp.output_lang, source, demo_id,
            analysis.topic_title, inp.explanation, inp.error_text, inp.code_snippet, model, C.PROMPT_VERSION,
            analysis.model_dump_json(), lesson.model_dump_json() if lesson else None, before,
        ),
    )
    gap_ids = {g.concept_id for g in gaps}
    for c in analysis.concepts:
        conn.execute(
            "INSERT INTO concept_results (attempt_id, concept_id, label, before_status, before_points, is_gap)"
            " VALUES (?,?,?,?,?,?)",
            (aid, c.id, c.label, c.status, points_for(c.status), int(c.id in gap_ids)),
        )
    conn.commit()
    return aid


def save_lesson(conn: sqlite3.Connection, attempt_id: str, lesson: LessonResult) -> None:
    conn.execute("UPDATE attempts SET lesson_json=? WHERE id=?", (lesson.model_dump_json(), attempt_id))
    conn.commit()


def save_proof(
    conn: sqlite3.Connection,
    attempt_id: str,
    retest: RetestSet,
    answers: dict[str, str],
    grades: dict[str, QuestionGrade],
    retest_points: dict[str, int],
    after: int,
) -> None:
    before = conn.execute("SELECT before_score FROM attempts WHERE id=?", (attempt_id,)).fetchone()["before_score"]
    conn.execute("UPDATE attempts SET after_score=?, delta=? WHERE id=?", (after, after - before, attempt_id))
    for q in retest.questions:
        g = grades.get(q.q_id)
        conn.execute(
            "INSERT OR REPLACE INTO retest_items (attempt_id, q_id, concept_id, type, question_json, answer, points,"
            " feedback, graded_by) VALUES (?,?,?,?,?,?,?,?,?)",
            (attempt_id, q.q_id, q.concept_id, q.type, q.model_dump_json(), answers.get(q.q_id),
             g.points if g else None, g.feedback if g else None, g.graded_by if g else None),
        )
    for cid, pts in retest_points.items():
        conn.execute(
            "UPDATE concept_results SET retested=1, after_points=? WHERE attempt_id=? AND concept_id=?",
            (pts, attempt_id, cid),
        )
    conn.commit()


def recent_attempts(conn: sqlite3.Connection, session_id: str, limit: int = 3) -> list[dict]:
    rows = conn.execute(
        "SELECT topic_title, before_score, after_score, created_at FROM attempts"
        " WHERE session_id=? AND after_score IS NOT NULL ORDER BY created_at DESC LIMIT ?",
        (session_id, limit),
    ).fetchall()
    return [dict(r) for r in rows]
