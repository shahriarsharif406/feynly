import pytest
from core.demo import DEMO_CASES, load_demo
from core.scoring import before_score, select_gaps, retest_targets, after_score
from core.validation import normalize

IDS = sorted({i for v in DEMO_CASES.values() for i in v})
EXPECT = {"photosynthesis_en": (50, 90), "indexerror_bn": (38, 88), "vaccines_en": (40, 80), "compound_interest_en": (30, 80)}


@pytest.mark.parametrize("did", IDS)
def test_case_integrity(did):
    c = load_demo(did)
    expl = normalize(c.input.explanation)
    for k in c.analysis.concepts:
        if k.evidence_quote:
            assert normalize(k.evidence_quote) in expl, (did, k.id)
    gaps = select_gaps(c.analysis.concepts)
    targets = retest_targets(c.analysis.concepts, gaps)
    assert [q.concept_id for q in c.retest.questions] == targets
    assert {g.concept_id for g in gaps} == {l.concept_id for l in c.lesson.lessons}


@pytest.mark.parametrize("did", EXPECT)
def test_expected_scores(did):
    c = load_demo(did)
    b = before_score(c.analysis.concepts)
    gaps = select_gaps(c.analysis.concepts)
    pts = {}
    for q in c.retest.questions:
        if q.type == "mcq":
            pts[q.concept_id] = 2 if c.sample_answers[q.q_id] == str(q.correct_option_index) else 0
        else:
            pts[q.concept_id] = c.grades[q.q_id].points
    assert (b, after_score(c.analysis.concepts, pts)) == EXPECT[did]
