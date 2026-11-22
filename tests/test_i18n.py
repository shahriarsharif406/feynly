import re, pathlib
from core.i18n import load_locales

ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_key_parity():
    loc = load_locales()
    assert set(loc["en"]) == set(loc["bn"])


def test_all_used_keys_exist():
    loc = load_locales()["en"]
    used = set()
    for p in list((ROOT / "ui").rglob("*.py")) + [ROOT / "app.py"]:
        used |= set(re.findall(r'\bt\(\s*"([a-z_0-9]+)"', p.read_text()))
    assert not (used - set(loc)), used - set(loc)
    for s in ("correct", "partial", "missing", "misconception"):
        assert f"status_{s}" in loc
    for b in ("cracked", "shaping", "mended", "golden"):
        assert f"band_{b}" in loc
