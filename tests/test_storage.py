from core.demo import load_demo
from core.pipeline import _state
from core.scoring import before_score, select_gaps
from core.storage import _connect, save_attempt, save_proof, progress_summary, class_summary
from core.models import QuestionGrade


def _save(conn, did, sess, code):
    c = load_demo(did)
    gaps = select_gaps(c.analysis.concepts)
    return c, save_attempt(conn, sess, c.input, c.analysis, gaps, c.lesson, before_score(c.analysis.concepts), "demo", did, None, code)


def test_class_and_progress():
    conn = _connect(":memory:")
    c, aid = _save(conn, "vaccines_en", "s1", "BIO-9A")
    _save(conn, "compound_interest_en", "s2", "BIO-9A")
    grades = {q.q_id: QuestionGrade(q_id=q.q_id, points=1, feedback="", matched_ideas=[], graded_by="demo") for q in c.retest.questions}
    save_proof(conn, aid, c.retest, {q.q_id: "x" for q in c.retest.questions}, grades,
               {q.concept_id: 1 for q in c.retest.questions}, 70)
    sm = class_summary(conn, "bio-9a")
    assert sm["attempts"] == 2 and sm["finished"] == 1 and sm["avg_after"] == 70
    assert sm["top_gaps"]
    assert class_summary(conn, "OTHER")["attempts"] == 0
    p = progress_summary(conn, "s1")
    assert len(p["loops"]) == 1 and p["open_gaps"]
