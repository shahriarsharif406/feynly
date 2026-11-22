# Evaluation (deterministic parts)

Reproduce with `python scripts/evaluate.py`. This covers scoring, quote verification and the offline grader on the 6 shipped demo cases. It does **not** measure Gemini's answer quality; that is judged by the live app.

| Case | Before | After | Gaps | Retest targets match gaps |
|---|---|---|---|---|
| compound_interest_en | 30 | 80 | 3 | yes |
| indexerror_bn | 38 | 88 | 3 | yes |
| indexerror_en | 38 | 88 | 3 | yes |
| photosynthesis_bn | 50 | 90 | 3 | yes |
| photosynthesis_en | 50 | 90 | 3 | yes |
| vaccines_en | 40 | 80 | 3 | yes |

- Evidence quotes found verbatim in the student text: **22/22**
- Offline keyword grader agrees with the reference grade on sample short answers: **6/12**
- Offline grader gave credit to junk answers ("I don't know", "banana", ...): **0/48**
- Scores are computed by Python only, so the same checkpoint statuses always give the same score.
