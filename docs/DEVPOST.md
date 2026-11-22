# Devpost submission text (Feynly)

## Tagline
Explain it. Fix it. Prove it.

## Inspiration
Most students can recite a topic but can't explain it. Tutors tell you the answer; they rarely show you, with evidence, that you actually understand it now. Feynly turns the Feynman technique into a loop that ends in proof.

## What it does
You explain a topic (or a bug) in your own words. Feynly finds the gaps, quoting your own sentences as evidence, teaches only those gaps in short lessons, then asks fresh questions and shows a before/after score. If you didn't improve, it says so honestly.

## How AI is used (Google Gemini)
Four Gemini calls: analyse the explanation into checkpoints, write short lessons for up to 3 gaps, generate new transfer questions, and grade the answers. The AI never computes scores: Python does, from checkpoint statuses. Every quoted "evidence" must appear verbatim in the student's text or it is discarded. Student text is treated as untrusted data. Retry, backoff and fallback-model logic keep it working on the free tier.

## How it was built
Python, Streamlit, Google Gemini (`google-genai`), pydantic, SQLite. Built with Claude Code (Anthropic): Claude wrote the architecture and code under my direction; I chose the idea, name and scope and reviewed the results.

## Features
- Concept mode and Bug-to-Lesson code mode
- English and Bangla
- Demo Mode with no API key (6 sample cases)
- Share image, progress view, teacher class view (no names stored), optional voice input
- Deterministic, auditable scoring; reproducible checks in `scripts/evaluate.py`

## Challenges
Making grading trustworthy: keeping scores out of the AI, verifying quotes, and handling failures without breaking the loop.

## What's next
More languages, saved classroom dashboards, spaced re-testing.

## Built with
python, streamlit, google-gemini, pydantic, sqlite, claude-code

## Links
- Code: https://github.com/shahriarsharif406/feynly
- Live demo: (add after deploy)
