"""Pre-recorded demo cases. These JSON files contain AI output only, never scores."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .models import DemoCase, LoopInput
from .validation import normalize

DEMO_DIR = Path(__file__).resolve().parent.parent / "data" / "demo"

DEMO_IDS: dict[tuple[str, str], str] = {
    ("concept", "en"): "photosynthesis_en",
    ("concept", "bn"): "photosynthesis_bn",
    ("code", "en"): "indexerror_en",
    ("code", "bn"): "indexerror_bn",
}

# Extra English sample cases shown in the Demo Mode picker (first id of each list is the default).
DEMO_CASES: dict[tuple[str, str], list[str]] = {
    ("concept", "en"): ["photosynthesis_en", "vaccines_en", "compound_interest_en"],
    ("concept", "bn"): ["photosynthesis_bn"],
    ("code", "en"): ["indexerror_en"],
    ("code", "bn"): ["indexerror_bn"],
}

_cache: dict[str, DemoCase] = {}


def load_demo(demo_id: str) -> DemoCase:
    if demo_id not in _cache:
        raw = (DEMO_DIR / f"{demo_id}.json").read_text(encoding="utf-8")
        _cache[demo_id] = DemoCase.model_validate(json.loads(raw))
    return _cache[demo_id].model_copy(deep=True)


def demo_ids_for(mode: str, lang: str) -> list[str]:
    return DEMO_CASES.get((mode, lang)) or [DEMO_IDS[(mode, lang)]]


def demo_for(mode: str, lang: str, demo_id: str | None = None) -> DemoCase:
    ids = demo_ids_for(mode, lang)
    return load_demo(demo_id if demo_id in ids else ids[0])


def match_demo_input(inp: LoopInput) -> Optional[DemoCase]:
    """A demo case matches when the explanation is exactly a sample explanation."""
    target = normalize(inp.explanation)
    for demo_id in {i for ids in DEMO_CASES.values() for i in ids}:
        case = load_demo(demo_id)
        if case.mode == inp.mode and normalize(case.input.explanation) == target:
            return case
    return None
