"""UI strings (English / Bangla). Missing keys fall back to English, then to the key itself."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

LOCALE_DIR = Path(__file__).resolve().parent.parent / "locales"
_BN_DIGITS = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")


@lru_cache(maxsize=1)
def load_locales() -> dict[str, dict[str, str]]:
    return {
        lang: json.loads((LOCALE_DIR / f"{lang}.json").read_text(encoding="utf-8"))
        for lang in ("en", "bn")
    }


def t(key: str, lang: str = "en", **fmt) -> str:
    loc = load_locales()
    s = loc.get(lang, {}).get(key) or loc["en"].get(key) or key
    try:
        return s.format(**fmt) if fmt else s
    except (KeyError, IndexError):
        return s


def status_label(status: str, lang: str = "en") -> str:
    return t(f"status_{status}", lang)


def band_label(band: str, lang: str = "en") -> str:
    return t(f"band_{band}", lang)


def to_bn_digits(n) -> str:
    return str(n).translate(_BN_DIGITS)


def num(n, lang: str) -> str:
    return to_bn_digits(n) if lang == "bn" else str(n)
