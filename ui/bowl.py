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


_DEFS = (
    "<defs>"
    '<linearGradient id="fyCoral" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFB27A"/><stop offset=".55" stop-color="#E0703F"/><stop offset="1" stop-color="#B2441C"/></linearGradient>'
    '<linearGradient id="fyGlass" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FFFFFF" stop-opacity=".16"/><stop offset="1" stop-color="#FFFFFF" stop-opacity=".04"/></linearGradient>'
    '<radialGradient id="fyHalo" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#E8B54A" stop-opacity=".35"/><stop offset="1" stop-color="#E8B54A" stop-opacity="0"/></radialGradient>'
    '<radialGradient id="fyShadow" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#000" stop-opacity=".55"/><stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient>'
    '<filter id="fyGlow" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="2.4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
    "</defs>"
)
DEPTH = 7


def _fill(status: str) -> tuple[str, str, str, str]:
    """(top fill, opacity, stroke, extrusion colour) for a status."""
    if status in ("correct", "misconception"):
        return "url(#fyCoral)", "1", "none", "#6E2B10"
    if status == "partial":
        return "url(#fyCoral)", "0.62", "none", "#4A2314"
    return "url(#fyGlass)", "1", "#8A93A8", "#1A2033"


def _svg_from_segs(segs: list[dict], score: int, size: int, band_text: str, score_text: str,
                   label: str = "") -> str:
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 220 220" width="{size}" height="{size}" '
        f'role="img" aria-label="{label or "Understanding score " + str(score) + " out of 100"}">',
        _DEFS,
        '<ellipse cx="110" cy="176" rx="92" ry="16" fill="url(#fyShadow)"/>',
        '<circle cx="110" cy="104" r="104" fill="url(#fyHalo)"/>',
        '<g transform="translate(0,20) scale(1,0.82)">',
    ]
    for s in segs:  # extrusion first so every top face sits above its neighbours' sides
        _, _, _, side = _fill(s["after"])
        parts.append(f'<path d="{s["d"]}" fill="{side}" transform="translate(0,{DEPTH})"/>')
    for s in segs:
        status = s["after"]
        fill, op, stroke, _ = _fill(status)
        dash = ' stroke-dasharray="4 3" stroke-width="1.5"' if stroke != "none" else ""
        parts.append(f'<path d="{s["d"]}" fill="{fill}" fill-opacity="{op}" stroke="{stroke}"{dash}/>')
        if stroke == "none":  # specular rim on lit surfaces
            parts.append(f'<path d="{s["d"]}" fill="none" stroke="#FFFFFF" stroke-opacity=".28" stroke-width="1"/>')
        if status == "misconception":
            parts.append(
                f'<path d="{s["crack"]}" fill="none" stroke="#2A0A08" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>'
                f'<path d="{s["crack"]}" fill="none" stroke="#FF6B6B" stroke-width="1.4" stroke-linejoin="round" stroke-linecap="round"/>'
            )
        elif s["retested"] and s["afterPoints"] >= 1 and s["before"] != s["after"]:
            half = ' stroke-dasharray="40 40"' if s["afterPoints"] == 1 else ""
            parts.append(
                f'<path d="{s["crack"]}" fill="none" stroke="#F2CF72" stroke-width="2.6" stroke-linecap="round" filter="url(#fyGlow)"{half}/>'
            )
    parts.append("</g>")
    parts.append(
        f'<text x="110" y="108" text-anchor="middle" font-family="Fraunces, Tiro Bangla, Georgia, serif" '
        f'font-size="44" font-weight="600" fill="#F6F1E4" stroke="#0B0F1A" stroke-width="3" paint-order="stroke">{score_text}</text>'
    )
    if band_text:
        parts.append(
            f'<text x="110" y="128" text-anchor="middle" font-family="Hind Siliguri, sans-serif" '
            f'font-size="12" fill="#B7BFD3">{band_text}</text>'
        )
    parts.append("</svg>")
    return "".join(parts)


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
    return _svg_from_segs(segs, score, size, band_text, score_text if score_text is not None else str(score))


def hero_bowl(size: int = 200) -> str:
    """Decorative bowl for the landing screen: mostly whole, one crack, one gold seam."""
    statuses = ["correct", "correct", "misconception", "partial", "correct", "missing"]
    n = len(statuses)
    segs = [
        {"d": segment_path(i, n), "crack": crack_path(i, n), "before": s, "after": s, "retested": False, "afterPoints": 0}
        for i, s in enumerate(statuses)
    ]
    segs[3].update(before="misconception", retested=True, afterPoints=2)
    return _svg_from_segs(segs, 0, size, "", "✦", label="Feynly concept bowl")
