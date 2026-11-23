"""Small HTML building blocks. All student-written text is escaped before it touches HTML."""
from __future__ import annotations

import html

import streamlit as st

from core.i18n import num, status_label, t
from core.models import Concept, GapRef, Lesson, ProofRow, ScoreBreakdown

def e(s) -> str:
    """HTML-escape, keeping newlines as entities so they survive line-collapsing in _html()."""
    return html.escape(str(s)).replace("\n", "&#10;")


def _html(s: str) -> None:
    # collapse indentation/blank lines so Streamlit's markdown never turns HTML into a code block
    st.markdown("".join(line.strip() for line in s.splitlines()), unsafe_allow_html=True)


_ICON = {
    "correct": '<svg width="12" height="12" viewBox="0 0 12 12"><path d="M2 6.5l2.6 2.6L10 3" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
    "partial": '<svg width="12" height="12" viewBox="0 0 12 12"><path d="M6 1a5 5 0 100 10z" fill="currentColor"/><circle cx="6" cy="6" r="4.6" fill="none" stroke="currentColor" stroke-width="1.2"/></svg>',
    "missing": '<svg width="12" height="12" viewBox="0 0 12 12"><circle cx="6" cy="6" r="4.6" fill="none" stroke="currentColor" stroke-width="1.4" stroke-dasharray="2 2"/></svg>',
    "misconception": '<svg width="12" height="12" viewBox="0 0 12 12"><path d="M1.5 2l3 3-2 2 3 3" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>',
}


def top_bar(lang: str, demo: bool) -> None:
    badge = (
        f'<span class="fy-badge demo" title="{e(t("badge_demo_tip", lang))}"><i></i>{e(t("badge_demo", lang))}</span>'
        if demo
        else f'<span class="fy-badge live" title="{e(t("badge_live_tip", lang))}"><i></i>{e(t("badge_live", lang))}</span>'
    )
    _html(
        f'<div class="fy-topbar" lang="{lang}"><div><div class="fy-wordmark">Feyn<span>ly</span></div>'
        f'<div class="fy-tagline">{e(t("tagline", lang))}</div></div>{badge}</div>'
    )


def stepper(stage: str, lang: str) -> None:
    idx = {"explain": 0, "gaps": 1, "proof": 2}[stage]
    names = [t("step_explain", lang), t("step_mend", lang), t("step_prove", lang)]
    xs = [70, 280, 490]
    parts = ['<svg class="fy-stepper" viewBox="0 0 560 64" width="100%" height="64" role="img" aria-label="progress">']
    parts.append(
        "<defs>"
        '<radialGradient id="sG" cx=".35" cy=".3" r=".8"><stop offset="0" stop-color="#FFF1B8"/><stop offset=".55" stop-color="#E8B54A"/><stop offset="1" stop-color="#A9701A"/></radialGradient>'
        '<radialGradient id="sD" cx=".35" cy=".3" r=".8"><stop offset="0" stop-color="#9BF0CB"/><stop offset=".55" stop-color="#3FB589"/><stop offset="1" stop-color="#1F6B50"/></radialGradient>'
        '<radialGradient id="sU" cx=".35" cy=".3" r=".8"><stop offset="0" stop-color="#4A5270"/><stop offset="1" stop-color="#161B2C"/></radialGradient>'
        '<filter id="sGlow" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="4"/></filter>'
        "</defs>"
    )
    parts.append('<path d="M70 26 L490 26" stroke="rgba(255,255,255,.14)" stroke-width="3" stroke-linecap="round" fill="none"/>')
    if idx > 0:
        parts.append(f'<path d="M70 26 L{xs[idx]} 26" stroke="#E8B54A" stroke-width="3" stroke-linecap="round" fill="none"/>')
    for i, (x, name) in enumerate(zip(xs, names)):
        grad = "sG" if i == idx else "sD" if i < idx else "sU"
        if i == idx:
            parts.append(f'<circle cx="{x}" cy="26" r="13" fill="#E8B54A" opacity=".55" filter="url(#sGlow)"/>')
        parts.append(f'<ellipse cx="{x}" cy="40" rx="9" ry="3" fill="#000" opacity=".45"/>')
        parts.append(f'<circle cx="{x}" cy="26" r="11" fill="url(#{grad})" stroke="rgba(255,255,255,.35)" stroke-width="1"/>')
        cls = "on" if i == idx else ""
        parts.append(f'<text x="{x}" y="12" text-anchor="middle" class="{cls}">{e(name)}</text>')
    parts.append("</svg>")
    _html("".join(parts))


def loader(placeholder, step_key: str, lang: str) -> None:
    placeholder.markdown(
        '<div class="fy-loader"><svg width="36" height="36" viewBox="0 0 34 34"><defs><radialGradient id="lG" cx=".35" cy=".3" r=".8">'
        '<stop offset="0" stop-color="#FFB27A"/><stop offset="1" stop-color="#B2441C"/></radialGradient></defs>'
        '<circle cx="17" cy="17" r="13" fill="url(#lG)"/>'
        '<path d="M17 4 A13 13 0 0 1 30 17" fill="none" stroke="#F2CF72" stroke-width="3" stroke-linecap="round"/></svg>'
        f'<p>{e(t(step_key, lang))}</p></div>',
        unsafe_allow_html=True,
    )


def banner(kind: str, text: str) -> None:
    _html(f'<div class="fy-banner {kind}" role="status">{e(text)}</div>')


def concept_chips(concepts: list[Concept], gaps: list[GapRef], lang: str) -> None:
    chips = []
    for c in concepts:
        chips.append(f'<span class="fy-chip {c.status}">{_ICON[c.status]}{e(c.label)}</span>')
    _html('<div class="fy-chips">' + "".join(chips) + "</div>")


def _dots(conf: str) -> str:
    n = {"low": 1, "medium": 2, "high": 3}[conf]
    return '<span class="fy-dots">' + "".join(f'<span class="{"f" if i < n else ""}"></span>' for i in range(3)) + "</span>"


_CRACK = '<svg class="crack" width="34" height="34" viewBox="0 0 34 34"><path d="M30 2 L22 12 L27 16 L17 28 L20 32" fill="none" stroke="#FF6B6B" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'


def fracture_card(concept: Concept, gap: GapRef, lang: str) -> None:
    tag = t({"misconception": "tag_misconception", "missing": "tag_missing", "partial": "tag_partial"}[gap.kind], lang)
    quote = ""
    if concept.evidence_quote:
        quote = f'<div class="fy-muted">{e(t("you_wrote", lang))}</div><div class="fy-quote">{e(concept.evidence_quote)}</div>'
    _html(
        f'<div class="fy-card fy-fracture {gap.kind}" lang="{lang}">{_CRACK}<span class="fy-tag">{e(tag)}</span>'
        f'<div class="fy-headline">{e(concept.gap_headline or concept.label)}</div>{quote}'
        f'<div>{e(concept.reason)}</div><div class="fy-muted" style="margin-top:6px">{e(t("confidence", lang))} {_dots(concept.confidence)}</div></div>'
    )


_SEAM = '<svg width="22" height="14" viewBox="0 0 22 14"><path d="M1 12 L7 3 L11 9 L16 2 L21 10" fill="none" stroke="#F2CF72" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>'


def mend_card(lesson: Lesson, lang: str) -> None:
    cf = ""
    if lesson.code_fix:
        cf = (
            f'<div class="fy-muted">{e(t("code_before", lang))}</div><div class="fy-code">{e(lesson.code_fix.before)}</div>'
            f'<div class="fy-muted">{e(t("code_after", lang))}</div><div class="fy-code">{e(lesson.code_fix.after)}</div>'
            f'<div class="fy-muted">{e(lesson.code_fix.explanation)}</div>'
        )
    _html(
        f'<div class="fy-card fy-mend" lang="{lang}"><h4>{_SEAM}{e(t("mend_title", lang, title=lesson.title))}</h4>'
        f'<div>{e(lesson.core_idea)}</div><div class="fy-muted" style="margin-top:6px">{e(lesson.example)}</div>'
        f'<div class="fy-cols"><div class="fy-said"><b>{e(t("you_said", lang))}</b>{e(lesson.you_said)}</div>'
        f'<div class="fy-actual"><b>{e(t("actually", lang))}</b>{e(lesson.actually)}</div></div>{cf}'
        f'<div class="fy-check">{e(t("check_yourself", lang))} {e(lesson.check_yourself)}</div></div>'
    )


def breakdown_table(bd: ScoreBreakdown, lang: str) -> None:
    rows = "".join(
        f'<tr><td>{e(cid)}</td><td>{e(label)}</td><td>{e(status_label(status, lang))}</td><td>{num(pts, lang)}</td></tr>'
        for cid, label, status, pts in bd.rows
    )
    _html(
        f'<table style="width:100%;font-size:15px;border-collapse:collapse"><tr><th align="left">{e(t("col_checkpoint", lang))}</th>'
        f'<th align="left"></th><th align="left">{e(t("col_status", lang))}</th><th align="left">{e(t("col_points", lang))}</th></tr>{rows}</table>'
        f'<div class="fy-muted" style="margin-top:6px">{e(t("formula_line", lang, pts=num(bd.total_points, lang), mx=num(bd.max_points, lang), score=num(bd.score, lang)))}</div>'
    )


def proof_strip(rows: list[ProofRow], lang: str) -> None:
    out = []
    for r in rows:
        verdict = (
            f'<div class="fy-still">{e(t("still_gap", lang))}</div>' if r.still_gap
            else f'<div class="fy-ok">{e(t("now_solid", lang))}</div>'
        )
        before_q = f'<small>“{e(r.before_quote[:90])}”</small>' if r.before_quote else ""
        out.append(
            f'<div class="fy-proof" lang="{lang}"><div><b>{e(r.label)}</b></div>'
            f'<div><span class="fy-chip {r.before_status}">{_ICON[r.before_status]}{e(status_label(r.before_status, lang))}</span>{before_q}</div>'
            f'<div><span class="fy-chip {r.after_status or "missing"}">{_ICON[r.after_status or "missing"]}{e(status_label(r.after_status or "missing", lang))}</span>'
            f'<small>{e(r.answer_snippet)}</small><small>{e(r.feedback)}</small>{verdict}</div></div>'
        )
    st.markdown("".join(out), unsafe_allow_html=True)


def disclaimer(lang: str) -> None:
    _html(f'<div class="fy-muted" lang="{lang}" style="margin-top:14px">{e(t("disclaimer", lang))}</div>')


def footer(lang: str) -> None:
    _html(f'<div class="fy-foot" lang="{lang}">{e(t("footer_credits", lang))}</div>')
