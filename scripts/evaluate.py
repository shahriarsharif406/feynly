"""Reproducible checks over the shipped demo cases. Run: python scripts/evaluate.py > docs/EVALUATION.md
Measures the deterministic parts of Feynly (no API key needed). It does not measure Gemini quality."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from core.demo import DEMO_CASES, load_demo
from core.offline_grader import grade_short, grade_mcq
from core.scoring import before_score, select_gaps, retest_targets, after_score
from core.validation import normalize

ids = sorted({i for v in DEMO_CASES.values() for i in v})
rows, q_ok, q_tot, agree, agree_tot, false_credit, junk_tot = [], 0, 0, 0, 0, 0, 0
JUNK = ["I don't know", "banana", "it depends on many things", "yes"]
for did in ids:
    c = load_demo(did)
    expl = normalize(c.input.explanation)
    for k in c.analysis.concepts:
        if k.evidence_quote:
            q_tot += 1
            q_ok += normalize(k.evidence_quote) in expl
    gaps = select_gaps(c.analysis.concepts)
    ok_t = [q.concept_id for q in c.retest.questions] == retest_targets(c.analysis.concepts, gaps)
    pts = {}
    for q in c.retest.questions:
        if q.type == "mcq":
            pts[q.concept_id] = grade_mcq(q, c.sample_answers[q.q_id]).points
            continue
        og = grade_short(q, c.sample_answers[q.q_id], c.language).points
        agree_tot += 1
        agree += og == c.grades[q.q_id].points
        pts[q.concept_id] = c.grades[q.q_id].points
        for j in JUNK:
            junk_tot += 1
            false_credit += grade_short(q, j, c.language).points > 0
    rows.append((did, before_score(c.analysis.concepts), after_score(c.analysis.concepts, pts), len(gaps), ok_t))

print("# Evaluation (deterministic parts)\n")
print("Reproduce with `python scripts/evaluate.py`. This covers scoring, quote verification and the offline grader on the "
      f"{len(ids)} shipped demo cases. It does **not** measure Gemini's answer quality; that is judged by the live app.\n")
print("| Case | Before | After | Gaps | Retest targets match gaps |\n|---|---|---|---|---|")
for r in rows:
    print(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {'yes' if r[4] else 'NO'} |")
print(f"\n- Evidence quotes found verbatim in the student text: **{q_ok}/{q_tot}**")
print(f"- Offline keyword grader agrees with the reference grade on sample short answers: **{agree}/{agree_tot}**")
print(f"- Offline grader gave credit to junk answers (\"I don't know\", \"banana\", ...): **{false_credit}/{junk_tot}**")
print("- Scores are computed by Python only, so the same checkpoint statuses always give the same score.")
