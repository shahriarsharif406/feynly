"""Downloadable proof card: one self-contained HTML page (A5 proportions)."""
from __future__ import annotations

import html

from core.i18n import band_label, num, status_label, t
from core.models import Concept, ProofRow
from core.scoring import band
from ui.bowl import bowl_svg

_CSS = """
body{margin:0;background:#F6F0E4;font-family:'Hind Siliguri',system-ui,sans-serif;color:#1E2433}
.card{max-width:560px;margin:24px auto;background:#FFFBF3;border:1px solid #E2D5C0;border-radius:16px;padding:28px}
.wm{font-family:'Fraunces','Tiro Bangla',Georgia,serif;font-size:26px;font-weight:600}.wm span{color:#C9952B}
h1{font-family:'Fraunces','Tiro Bangla',Georgia,serif;font-size:24px;margin:14px 0 2px}
.muted{color:#5B6274;font-size:14px}.hero{display:flex;align-items:center;gap:18px;margin:14px 0}
.delta{background:#C9952B;color:#1E2433;font-family:'Fraunces',Georgia,serif;font-weight:600;font-size:24px;padding:4px 16px;border-radius:999px}
.row{border-top:1px dashed #E2D5C0;padding:10px 0;font-size:15px}.still{color:#9E2B25;font-weight:600}.ok{color:#2E6B57;font-weight:600}
.foot{margin-top:16px;border-top:1px solid #E2D5C0;padding-top:12px;font-size:13px;color:#5B6274}
"""


def build_proof_html(
    topic: str,
    lang: str,
    before: int,
    after: int,
    rows: list[ProofRow],
    created_at: str,
    concepts: list[Concept] | None = None,
    retest_points: dict[str, int] | None = None,
) -> str:
    e = html.escape
    bowl = ""
    if concepts is not None:
        bowl = bowl_svg(concepts, retest_points, after, size=150, band_text=e(band_label(band(after), lang)),
                        score_text=num(after, lang))
    delta = after - before
    d_txt = ("+" if delta >= 0 else "−") + num(abs(delta), lang)
    body = []
    for r in rows:
        tag = (
            f'<span class="still">{e(t("still_gap", lang))}</span>' if r.still_gap
            else f'<span class="ok">{e(t("now_solid", lang))}</span>'
        )
        body.append(
            f'<div class="row"><b>{e(r.label)}</b> · {tag}<br>'
            f'<span class="muted">{e(status_label(r.before_status, lang))} → '
            f'{e(status_label(r.after_status or "missing", lang))}</span><br>'
            f'<span class="muted">{e(r.answer_snippet)}</span></div>'
        )
    return (
        f'<!doctype html><html lang="{e(lang)}"><head><meta charset="utf-8"><title>Feynly proof card</title>'
        "<style>@import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@600&family=Hind+Siliguri:wght@400;600"
        f"&family=Tiro+Bangla&display=swap');{_CSS}</style></head><body><div class=\"card\">"
        '<div class="wm">Feyn<span>ly</span></div>'
        f'<h1>{e(topic)}</h1><div class="muted">{e(created_at[:10])}</div>'
        f'<div class="hero">{bowl}<div><div class="muted">{e(t("before", lang))} {num(before, lang)} → '
        f'{e(t("after", lang))} {num(after, lang)}</div><div class="delta">{e(d_txt)}</div></div></div>'
        + "".join(body)
        + f'<div class="foot">{e(t("disclaimer", lang))}<br>{e(t("proof_footer", lang))}</div></div></body></html>'
    )
