"""The Concept Bowl: one ring segment per checkpoint. Gaps are cracks; mended gaps get gold seams."""
from __future__ import annotations

import math

from core.models import Concept
from core.scoring import points_for, status_from_points

CX = CY = 110
R_OUT, R_IN = 92, 56
GAP_DEG = 3.0


def _pt(r: float, deg: float) -> tuple[float, float]:
    a = math.radians(deg - 90)
    return CX + r * math.cos(a), CY + r * math.sin(a)


def segment_path(i: int, n: int) -> str:
    span = 360 / n
    a0, a1 = i * span + GAP_DEG / 2, (i + 1) * span - GAP_DEG / 2
    x0, y0 = _pt(R_OUT, a0)
    x1, y1 = _pt(R_OUT, a1)
    x2, y2 = _pt(R_IN, a1)
    x3, y3 = _pt(R_IN, a0)
    large = 1 if (a1 - a0) > 180 else 0
    return (
        f"M{x0:.1f},{y0:.1f} A{R_OUT},{R_OUT} 0 {large} 1 {x1:.1f},{y1:.1f} "
        f"L{x2:.1f},{y2:.1f} A{R_IN},{R_IN} 0 {large} 0 {x3:.1f},{y3:.1f} Z"
    )


def crack_path(i: int, n: int) -> str:
    """Deterministic zigzag across the middle of segment i (no randomness: renders are stable)."""
    mid = (i + 0.5) * 360 / n
    pts = []
    steps = 5
    for k in range(steps + 1):
        r = R_IN + 4 + (R_OUT - R_IN - 8) * k / steps
        off = 0 if k in (0, steps) else (5 + (i + k) % 3) * (1 if k % 2 else -1)
        pts.append(_pt(r, mid + off / (r / 60)))
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)


def segment_data(concepts: list[Concept], retest_points: dict[str, int] | None) -> list[dict]:
    n = len(concepts)
    out = []
    for i, c in enumerate(concepts):
        before_pts = points_for(c.status)
        retested = bool(retest_points) and c.id in retest_points
        after_pts = retest_points[c.id] if retested else before_pts
        out.append(
            {
                "id": c.id,
                "d": segment_path(i, n),
                "crack": crack_path(i, n),
                "before": c.status,
                "after": status_from_points(after_pts) if retested else c.status,
                "retested": retested,
                "afterPoints": after_pts,
            }
        )
    return out


def _fill(status: str) -> tuple[str, str, str]:
    """(fill, opacity, stroke) for a status."""
    if status == "correct":
        return "#A9542F", "1", "none"
    if status == "partial":
        return "#A9542F", "0.6", "none"
    if status == "misconception":
        return "#A9542F", "1", "none"
    return "#EFE6D4", "1", "#8C93A3"


def bowl_svg(
    concepts: list[Concept],
    retest_points: dict[str, int] | None,
    score: int,
    size: int = 220,
    band_text: str = "",
    score_text: str | None = None,
    animated: bool = False,
) -> str:
    segs = segment_data(concepts, retest_points)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 220 220" width="{size}" height="{size}" '
        f'role="img" aria-label="Understanding score {score} out of 100">'
    ]
    for s in segs:
        status = s["after"]
        fill, op, stroke = _fill(status)
        dash = ' stroke-dasharray="4 3" stroke-width="1.5"' if stroke != "none" else ""
        parts.append(f'<path d="{s["d"]}" fill="{fill}" fill-opacity="{op}" stroke="{stroke}"{dash}/>')
        if status == "misconception":
            parts.append(
                f'<path d="{s["crack"]}" fill="none" stroke="#9E2B25" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round"/>'
            )
        elif s["retested"] and s["afterPoints"] >= 1 and s["before"] != s["after"]:
            half = ' stroke-dasharray="40 40"' if s["afterPoints"] == 1 else ""
            parts.append(
                f'<path d="{s["crack"]}" fill="none" stroke="#C9952B" stroke-width="2.5" stroke-linecap="round"{half}/>'
            )
    st = score_text if score_text is not None else str(score)
    parts.append(
        f'<text x="110" y="116" text-anchor="middle" font-family="Fraunces, Tiro Bangla, Georgia, serif" '
        f'font-size="44" font-weight="600" fill="#1E2433">{st}</text>'
    )
    if band_text:
        parts.append(
            f'<text x="110" y="136" text-anchor="middle" font-family="Hind Siliguri, sans-serif" '
            f'font-size="12" fill="#5B6274">{band_text}</text>'
        )
    parts.append("</svg>")
    return "".join(parts)
