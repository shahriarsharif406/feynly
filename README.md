# Feynly: Explain it. Fix it. Prove it.

Feynly checks whether you really understand something. You explain a topic (or a bug) in your own words, Feynly finds the gaps, teaches only those gaps, then asks fresh questions and shows measurable before/after proof.

**Loop:** Explain → Diagnose (3–5 checkpoints) → Mend (short lessons on ≤3 gaps) → Retest (new questions) → Prove (score before vs after).

- **Honest scoring:** scores are computed by Python from checkpoint statuses, never by the AI. Negative change is shown as it is.
- **Grounded:** every claimed misconception must quote your own words, verified in code.
- **Bangla + English** UI and lessons. Concept mode and Bug-to-Lesson code mode.
- **Share it:** download a share image (SVG) and copy-ready text of your before/after.
- **Progress + class view:** see the gaps that keep coming back; teachers can view class-wide common gaps via a shared class code (no names stored).
- **Voice (optional, Live AI):** speak your explanation, review the transcript, then use it.
- **Works without a key:** Demo Mode ships 4 pre-made cases so anyone can try it instantly.

## Run locally
```
pip install -r requirements.txt
streamlit run app.py
```
Optional: set `GEMINI_API_KEY` (free Google AI Studio key) in `.streamlit/secrets.toml` or the environment for Live AI.

## Evaluation
`python scripts/evaluate.py` checks scoring, quote verification and the offline grader on the demo cases (see `docs/EVALUATION.md`). Honest note: the offline keyword grader is only a fallback and agrees with reference grades on about half of short answers; Live AI grading is the intended path.

## Tests
```
pip install -r requirements-dev.txt && pytest
```

## Stack
Streamlit, Google Gemini (`google-genai`), pydantic, SQLite. Built with Claude Code.

## Disclaimer
A study aid. The score reflects one explanation, not overall ability.

MIT License.
