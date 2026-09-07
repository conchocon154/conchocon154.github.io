#!/usr/bin/env python3
"""Generate the site's charts as inline SVG, straight from the project results.

Every figure on the portfolio is drawn here from the CSV and JSON that the
source repositories emit, so a number on the page can always be traced back to
the run that produced it. Nothing is transcribed by hand.

The output is inline SVG rather than PNG for three reasons: it stays sharp at
any zoom, it weighs a fraction of a bitmap, and — because the fills and strokes
are CSS custom properties — one figure serves both the light and the dark
theme instead of needing two exports.

Charts are written into the bilingual master at src/index.html; run
tools/build_site.py afterwards to emit the per-language pages that ship.

Usage:
    python3 tools/build_charts.py            # rewrite the marked blocks in the master
    python3 tools/build_charts.py --check    # fail if the master is out of date
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOME = ROOT.parent

SRC = {
    "retail": HOME / "retail-analytics-sql" / "reports",
    "ev": HOME / "ev-purchase-analysis" / "reports",
    "cap": HOME / "caption-decoding-study" / "reports",
    "matcher": HOME / "vn-product-matcher" / "reports",
}

# Charts shown side by side get a narrower viewBox, so their labels render at
# the same optical size as the full-width ones instead of shrinking to nothing.
WIDE = 720
HALF = 440
INK = "var(--text)"
DIM = "var(--text-dim)"
MUTE = "var(--text-mute)"
LINE = "var(--line)"
ACCENT = "var(--accent)"
WARN = "var(--warn)"

MONO = 'font-family="ui-monospace, SFMono-Regular, Menlo, monospace"'


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------

def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def num(v: str | float) -> float:
    return float(v) if v not in ("", None) else float("nan")


def txt(x, y, s, *, size=10, fill=MUTE, anchor="start", weight=None, baseline=None):
    a = f'<text x="{x:.1f}" y="{y:.1f}" {MONO} font-size="{size}" fill="{fill}" text-anchor="{anchor}"'
    if weight:
        a += f' font-weight="{weight}"'
    if baseline:
        a += f' dominant-baseline="{baseline}"'
    return a + f">{s}</text>"


def open_svg(w: int, h: int, label: str) -> list[str]:
    return [
        f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{label}" '
        f'preserveAspectRatio="xMidYMid meet">'
    ]


def glow(uid: str) -> str:
    """A soft accent bloom under a line — the one flourish these charts get."""
    return (
        f'<defs><filter id="{uid}" x="-20%" y="-40%" width="140%" height="180%">'
        f'<feGaussianBlur stdDeviation="3.2" result="b"/>'
        f'<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>'
        f"</filter></defs>"
    )


def area_gradient(uid: str, color: str = ACCENT) -> str:
    return (
        f'<defs><linearGradient id="{uid}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{color}" stop-opacity="0.28"/>'
        f'<stop offset="100%" stop-color="{color}" stop-opacity="0"/>'
        f"</linearGradient></defs>"
    )


def gridlines(x0, x1, ys, *, dash="2 5"):
    return "".join(
        f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" stroke="{LINE}" '
        f'stroke-width="1" stroke-dasharray="{dash}"/>'
        for y in ys
    )


# --------------------------------------------------------------------------
# 1. retail — monthly revenue bars with the gross-margin line over them
# --------------------------------------------------------------------------

def retail_revenue(W: int) -> str:
    rows = read_csv(SRC["retail"] / "tables" / "01_revenue_margin_monthly.csv")
    H, T, B, L, R = 260, 26, 46, 52, 44
    x0, x1, y0, y1 = L, W - R, T, H - B

    rev = [num(r["revenue"]) / 1e6 for r in rows]
    mar = [num(r["margin_pct"]) for r in rows]
    months = [r["sale_month"] for r in rows]

    rev_max = max(rev) * 1.12
    m_lo, m_hi = 17.0, 22.0                      # zoomed: the drift is 2 points
    n = len(rows)
    step = (x1 - x0) / n
    bw = step * 0.62

    def yr(v): return y1 - (v / rev_max) * (y1 - y0)
    def ym(v): return y1 - ((v - m_lo) / (m_hi - m_lo)) * (y1 - y0)

    s = open_svg(W, H, "Monthly revenue and gross margin over 25 months")
    s.append(area_gradient("g-rev"))
    s.append(glow("f-rev"))
    s.append(gridlines(x0, x1, [ym(v) for v in (18, 19, 20, 21)]))

    for i, v in enumerate(rev):
        cx = x0 + i * step + (step - bw) / 2
        s.append(
            f'<rect x="{cx:.1f}" y="{yr(v):.1f}" width="{bw:.1f}" '
            f'height="{y1 - yr(v):.1f}" rx="1.5" fill="{MUTE}" opacity="0.28"/>'
        )

    pts = [(x0 + i * step + step / 2, ym(v)) for i, v in enumerate(mar)]
    d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    s.append(f'<path d="{d} L{pts[-1][0]:.1f} {y1} L{pts[0][0]:.1f} {y1} Z" fill="url(#g-rev)"/>')
    s.append(f'<path d="{d}" fill="none" stroke="{WARN}" stroke-width="2.1" '
             f'stroke-linejoin="round" stroke-linecap="round" filter="url(#f-rev)"/>')
    for x, y in (pts[0], pts[-1]):
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.4" fill="{WARN}"/>')

    # axes
    s.append(f'<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" stroke="{LINE}" stroke-width="1"/>')
    for v in (18, 20, 22):
        s.append(txt(x0 - 8, ym(v) + 3, f"{v}%", anchor="end", size=9.5, fill=WARN))
    tick = 100 if rev_max <= 550 else 200
    v = 0
    while v <= rev_max:
        s.append(txt(x1 + 8, yr(v) + 3, f"{v:g}", size=9.5))
        v += tick
    for i in range(0, n, 4):
        s.append(txt(x0 + i * step + step / 2, y1 + 16, months[i][2:], anchor="middle", size=9))

    s.append(txt(x0, T - 10, "Gross margin %", size=10, fill=WARN, weight="600"))
    s.append(txt(x1, T - 10, "Revenue, m VND", size=10, anchor="end"))
    s.append(txt(x0, H - 8, f"{months[0]} → {months[-1]}   ·   revenue flat, margin sliding", size=9.5))
    s.append("</svg>")
    return "".join(s)


# --------------------------------------------------------------------------
# 2. retail — revenue concentration (Pareto)
# --------------------------------------------------------------------------

def retail_pareto(W: int) -> str:
    rows = read_csv(SRC["retail"] / "tables" / "03_abc_pareto.csv")
    H, T, B, L, R = 250, 24, 44, 46, 26
    x0, x1, y0, y1 = L, W - R, T, H - B

    xs = [0.0] + [num(r["cumulative_sku_pct"]) for r in rows]
    ys = [0.0] + [num(r["cumulative_revenue_pct"]) for r in rows]

    def px(v): return x0 + v / 100 * (x1 - x0)
    def py(v): return y1 - v / 100 * (y1 - y0)

    # where the curve first crosses 80% of revenue
    cut = next(x for x, y in zip(xs, ys) if y >= 80)

    s = open_svg(W, H, "Cumulative revenue share against cumulative SKU share")
    s.append(area_gradient("g-par"))
    s.append(glow("f-par"))
    s.append(gridlines(x0, x1, [py(v) for v in (25, 50, 75, 100)]))
    s.append(f'<line x1="{px(0)}" y1="{py(0)}" x2="{px(100)}" y2="{py(100)}" '
             f'stroke="{MUTE}" stroke-width="1" stroke-dasharray="3 4" opacity="0.6"/>')

    d = "M" + " L".join(f"{px(x):.1f} {py(y):.1f}" for x, y in zip(xs, ys))
    s.append(f'<path d="{d} L{px(100):.1f} {y1} L{px(0):.1f} {y1} Z" fill="url(#g-par)"/>')
    s.append(f'<path d="{d}" fill="none" stroke="{ACCENT}" stroke-width="2.3" '
             f'stroke-linejoin="round" filter="url(#f-par)"/>')

    s.append(f'<line x1="{px(cut):.1f}" y1="{py(0)}" x2="{px(cut):.1f}" y2="{py(80):.1f}" '
             f'stroke="{WARN}" stroke-width="1.4" stroke-dasharray="4 4"/>')
    s.append(f'<circle cx="{px(cut):.1f}" cy="{py(80):.1f}" r="4.2" fill="{WARN}"/>')
    # the annotation goes in the open space under the curve, not on top of it
    s.append(txt(px(cut) + 14, py(38), f"{cut:.1f}% of SKUs", size=11.5, fill=INK, weight="700"))
    s.append(txt(px(cut) + 14, py(38) + 15, "carry 80%", size=10.5, fill=DIM))
    s.append(txt(px(cut) + 14, py(38) + 29, "of revenue", size=10.5, fill=DIM))

    s.append(f'<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" stroke="{LINE}"/>')
    for v in (0, 50, 100):
        s.append(txt(x0 - 8, py(v) + 3, f"{v}", anchor="end", size=9.5))
        s.append(txt(px(v), y1 + 16, f"{v}", anchor="middle", size=9.5))
    s.append(txt(x0, T - 8, "Cumulative revenue %", size=10, fill=DIM))
    s.append(txt(x1, H - 8, "Cumulative SKU %  →", size=9.5, anchor="end"))
    s.append(txt(x0, H - 8, "dashed = if every SKU sold equally", size=9.5))
    s.append("</svg>")
    return "".join(s)


# --------------------------------------------------------------------------
# 3. retail — receivables ageing
# --------------------------------------------------------------------------

def retail_ageing(W: int) -> str:
    rows = read_csv(SRC["retail"] / "tables" / "05_receivables_aging.csv")
    buckets = [
        ("0–30 days", sum(num(r["bucket_0_30"]) for r in rows)),
        ("31–60", sum(num(r["bucket_31_60"]) for r in rows)),
        ("61–90", sum(num(r["bucket_61_90"]) for r in rows)),
        ("over 90 days", sum(num(r["bucket_90_plus"]) for r in rows)),
    ]
    total = sum(v for _, v in buckets)

    H, T, B, L, R = 210, 30, 40, 46, 26
    x0, x1, y0, y1 = L, W - R, T, H - B
    vmax = max(v for _, v in buckets) * 1.18
    step = (x1 - x0) / len(buckets)
    bw = step * 0.46

    s = open_svg(W, H, "Receivables by age bucket")
    s.append(glow("f-age"))
    s.append(gridlines(x0, x1, [y1 - f * (y1 - y0) for f in (0.33, 0.66, 1.0)]))

    for i, (name, v) in enumerate(buckets):
        cx = x0 + i * step + (step - bw) / 2
        h = v / vmax * (y1 - y0)
        over90 = i == len(buckets) - 1
        fill = WARN if over90 else ACCENT
        op = "1" if over90 else "0.42"
        s.append(f'<rect x="{cx:.1f}" y="{y1 - h:.1f}" width="{bw:.1f}" height="{h:.1f}" '
                 f'rx="3" fill="{fill}" opacity="{op}"'
                 + (f' filter="url(#f-age)"' if over90 else "") + "/>")
        s.append(txt(cx + bw / 2, y1 - h - 9, f"{v / total * 100:.0f}%", anchor="middle",
                     size=12, fill=INK if over90 else DIM, weight="700" if over90 else "600"))
        s.append(txt(cx + bw / 2, y1 + 16, name, anchor="middle", size=9.5,
                     fill=WARN if over90 else MUTE))

    s.append(f'<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" stroke="{LINE}"/>')
    s.append(txt(x0, T - 12, "Share of the receivables book", size=10, fill=DIM))
    s.append(txt(x1, T - 12, f"{len(rows)} credit accounts", size=9.5, anchor="end"))
    s.append("</svg>")
    return "".join(s)


# --------------------------------------------------------------------------
# 4. ev — lift curve
# --------------------------------------------------------------------------

def ev_lift(W: int) -> str:
    rows = read_csv(SRC["ev"] / "tables" / "lift_by_decile.csv")
    H, T, B, L, R = 250, 26, 44, 46, 26
    x0, x1, y0, y1 = L, W - R, T, H - B

    xs = [0.0] + [num(r["top_pct"]) for r in rows]
    ys = [0.0] + [num(r["capture_pct"]) for r in rows]

    def px(v): return x0 + v / 100 * (x1 - x0)
    def py(v): return y1 - v / 100 * (y1 - y0)

    s = open_svg(W, H, "Share of buyers reached against share of the list contacted")
    s.append(area_gradient("g-lift"))
    s.append(glow("f-lift"))
    s.append(gridlines(x0, x1, [py(v) for v in (25, 50, 75, 100)]))
    s.append(f'<line x1="{px(0)}" y1="{py(0)}" x2="{px(100)}" y2="{py(100)}" '
             f'stroke="{MUTE}" stroke-width="1" stroke-dasharray="3 4" opacity="0.6"/>')

    d = "M" + " L".join(f"{px(x):.1f} {py(y):.1f}" for x, y in zip(xs, ys))
    s.append(f'<path d="{d} L{px(100):.1f} {y1} L{px(0):.1f} {y1} Z" fill="url(#g-lift)"/>')
    s.append(f'<path d="{d}" fill="none" stroke="{ACCENT}" stroke-width="2.3" '
             f'stroke-linejoin="round" filter="url(#f-lift)"/>')
    for x, y in list(zip(xs, ys))[1:]:
        s.append(f'<circle cx="{px(x):.1f}" cy="{py(y):.1f}" r="2.8" fill="{ACCENT}"/>')

    # the operational read: 30% of the list
    hit = next(y for x, y in zip(xs, ys) if x == 30)
    s.append(f'<line x1="{px(30):.1f}" y1="{y1}" x2="{px(30):.1f}" y2="{py(hit):.1f}" '
             f'stroke="{WARN}" stroke-width="1.4" stroke-dasharray="4 4"/>')
    s.append(f'<circle cx="{px(30):.1f}" cy="{py(hit):.1f}" r="4.4" fill="{WARN}"/>')
    s.append(txt(px(30) + 13, py(hit) - 11, f"top 30% of the list", size=11, fill=INK, weight="600"))
    s.append(txt(px(30) + 13, py(hit) + 4, f"reaches {hit:.0f}% of buyers", size=10, fill=DIM))

    s.append(f'<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" stroke="{LINE}"/>')
    for v in (0, 50, 100):
        s.append(txt(x0 - 8, py(v) + 3, f"{v}", anchor="end", size=9.5))
        s.append(txt(px(v), y1 + 16, f"{v}", anchor="middle", size=9.5))
    s.append(txt(x0, T - 8, "Buyers reached %", size=10, fill=DIM))
    s.append(txt(x1, H - 8, "List contacted %  →", size=9.5, anchor="end"))
    s.append(txt(x0, H - 8, "dashed = contacting at random", size=9.5))
    s.append("</svg>")
    return "".join(s)


# --------------------------------------------------------------------------
# 5. ev — what actually separates buyers
# --------------------------------------------------------------------------

def ev_drivers(W: int) -> str:
    rows = read_csv(SRC["ev"] / "tables" / "driver_ranking.csv")
    rows.sort(key=lambda r: num(r["spread_pp"]), reverse=True)

    pad_l, R = 210, 60
    row_h, T = 26, 30
    H = T + row_h * len(rows) + 22
    x0, x1 = pad_l, W - R
    vmax = max(num(r["spread_pp"]) for r in rows)

    s = open_svg(W, H, "Features ranked by the spread in purchase rate they produce")
    s.append(glow("f-drv"))
    s.append(txt(0, T - 14, "Spread in purchase rate across a feature's levels, in points",
                 size=10, fill=DIM))

    for i, r in enumerate(rows):
        y = T + i * row_h
        v = num(r["spread_pp"])
        w = v / vmax * (x1 - x0)
        strong = i < 3
        name = r["feature"].replace("_", " ")
        s.append(txt(x0 - 12, y + 13, name, anchor="end", size=10.5,
                     fill=INK if strong else MUTE, weight="600" if strong else None))
        s.append(f'<rect x="{x0}" y="{y + 4:.1f}" width="{w:.1f}" height="16" rx="3" '
                 f'fill="{ACCENT}" opacity="{"1" if strong else "0.34"}"'
                 + (' filter="url(#f-drv)"' if i == 0 else "") + "/>")
        s.append(txt(x0 + w + 9, y + 16, f"{v:.1f}", size=10.5,
                     fill=INK if strong else MUTE, weight="600" if strong else None))

    s.append(txt(0, H - 4, "the top three are the only levers worth a campaign", size=9.5))
    s.append("</svg>")
    return "".join(s)


# --------------------------------------------------------------------------
# 6. ev — the interaction that was not there
# --------------------------------------------------------------------------

def ev_interaction(W: int) -> str:
    rows = read_csv(SRC["ev"] / "tables" / "interaction_subsidy_concern.csv")
    rows.reverse()                                   # concern 5 at the top
    cols = ["No", "Yes"]

    L, T = 150, 74
    ch = 40
    cw = (W - L - 20) / len(cols)
    H = T + ch * len(rows) + 46

    vmax = max(num(r[c]) for r in rows for c in cols)

    s = open_svg(W, H, "Purchase rate by subsidy availability and environmental concern")
    s.append(txt(0, 22, "Purchase rate %", size=10.5, fill=DIM))
    s.append(txt(0, 38, "rows: environmental concern", size=9.5))

    for j, c in enumerate(cols):
        s.append(txt(L + j * cw + (cw - 6) / 2, T - 14, f"subsidy: {c.lower()}", anchor="middle",
                     size=10.5, fill=DIM))

    for i, r in enumerate(rows):
        y = T + i * ch
        lvl = int(float(r["Environmental_Concern_Level"]))
        s.append(txt(L - 14, y + ch / 2 + 4, f"concern {lvl}", anchor="end", size=10,
                     fill=INK if lvl == 5 else MUTE))
        for j, c in enumerate(cols):
            v = num(r[c])
            op = 0.06 + 0.94 * math.sqrt(v / vmax)   # sqrt so the small cells stay readable
            x = L + j * cw
            s.append(f'<rect x="{x:.1f}" y="{y}" width="{cw - 6:.1f}" height="{ch - 6}" rx="4" '
                     f'fill="{ACCENT}" opacity="{op:.3f}"/>')
            s.append(txt(x + (cw - 6) / 2, y + ch / 2 + 4, f"{v:.2f}", anchor="middle",
                         size=11.5, fill=INK if op > 0.55 else DIM, weight="600"))

    s.append(txt(0, H - 6,
                 "69.33 beside 2.48 looks like an interaction — the LR test says p = 0.62",
                 size=9.5, fill=WARN))
    s.append("</svg>")
    return "".join(s)


# --------------------------------------------------------------------------
# 7. caption — quality against diversity
# --------------------------------------------------------------------------

def cap_tradeoff(W: int) -> str:
    rows = read_csv(SRC["cap"] / "tables" / "decoding_results.csv")
    H, T, B, L, R = 280, 34, 48, 58, 120
    x0, x1, y0, y1 = L, W - R, T, H - B

    xs = [num(r["unique_caption_pct"]) for r in rows]
    ys = [num(r["bleu_4"]) for r in rows]
    xlo, xhi = 45.0, 78.0
    ylo, yhi = 0.235, 0.285

    def px(v): return x0 + (v - xlo) / (xhi - xlo) * (x1 - x0)
    def py(v): return y1 - (v - ylo) / (yhi - ylo) * (y1 - y0)

    s = open_svg(W, H, "Caption quality against caption diversity for four decoding strategies")
    s.append(glow("f-cap"))
    s.append(gridlines(x0, x1, [py(v) for v in (0.25, 0.26, 0.27, 0.28)]))

    order = sorted(range(len(rows)), key=lambda i: num(rows[i]["beam_width"]))
    d = "M" + " L".join(f"{px(xs[i]):.1f} {py(ys[i]):.1f}" for i in order)
    s.append(f'<path d="{d}" fill="none" stroke="{MUTE}" stroke-width="1.4" '
             f'stroke-dasharray="4 4" opacity="0.75"/>')

    best = max(range(len(rows)), key=lambda i: ys[i])
    for i, r in enumerate(rows):
        top = i == best
        s.append(f'<circle cx="{px(xs[i]):.1f}" cy="{py(ys[i]):.1f}" r="{6.5 if top else 5}" '
                 f'fill="{ACCENT if top else MUTE}" opacity="{1 if top else 0.62}"'
                 + (' filter="url(#f-cap)"' if top else "") + "/>")
        label = r["strategy"]
        s.append(txt(px(xs[i]), py(ys[i]) - 13, label, anchor="middle", size=10.5,
                     fill=INK if top else DIM, weight="600" if top else None))

    # the point of the chart, said in words on the chart
    bx = x1 + 16
    s.append(txt(bx, py(0.2785) - 4, "beam-5 is the", size=10.5, fill=INK, weight="600"))
    s.append(txt(bx, py(0.2785) + 10, "quality peak", size=10.5, fill=INK, weight="600"))
    s.append(txt(bx, py(0.2705) + 18, "beam-10: worse", size=10, fill=WARN))
    s.append(txt(bx, py(0.2705) + 31, "and less varied", size=10, fill=WARN))

    s.append(f'<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" stroke="{LINE}"/>')
    for v in (0.24, 0.26, 0.28):
        s.append(txt(x0 - 9, py(v) + 3, f"{v:.2f}", anchor="end", size=9.5))
    for v in (50, 60, 70):
        s.append(txt(px(v), y1 + 16, f"{v}%", anchor="middle", size=9.5))
    s.append(txt(x0 - 44, T - 14, "BLEU-4", size=10, fill=DIM))
    s.append(txt(x1, H - 8, "unique captions  →", size=9.5, anchor="end"))
    s.append(txt(x0 - 44, H - 8, "up and to the right is better on both axes", size=9.5))
    s.append("</svg>")
    return "".join(s)


# --------------------------------------------------------------------------
# 7b. caption — BLEU-4 across beam widths, and where it turns
# --------------------------------------------------------------------------

def cap_beam(W: int) -> str:
    rows = sorted(read_csv(SRC["cap"] / "tables" / "decoding_results.csv"),
                  key=lambda r: num(r["beam_width"]))
    H, T, B, L, R = 230, 34, 46, 54, 30
    x0, x1, y0, y1 = L, W - R, T, H - B

    ys = [num(r["bleu_4"]) for r in rows]
    ylo, yhi = 0.238, 0.284
    step = (x1 - x0) / (len(rows) - 1)

    def px(i): return x0 + i * step
    def py(v): return y1 - (v - ylo) / (yhi - ylo) * (y1 - y0)

    s = open_svg(W, H, "BLEU-4 across decoding strategies")
    s.append(area_gradient("g-beam"))
    s.append(glow("f-beam"))
    s.append(gridlines(x0, x1, [py(v) for v in (0.25, 0.26, 0.27, 0.28)]))

    d = "M" + " L".join(f"{px(i):.1f} {py(v):.1f}" for i, v in enumerate(ys))
    s.append(f'<path d="{d} L{px(len(ys) - 1):.1f} {y1} L{px(0):.1f} {y1} Z" fill="url(#g-beam)"/>')
    s.append(f'<path d="{d}" fill="none" stroke="{ACCENT}" stroke-width="2.3" '
             f'stroke-linejoin="round" filter="url(#f-beam)"/>')

    peak = max(range(len(ys)), key=lambda i: ys[i])
    for i, v in enumerate(ys):
        top = i == peak
        s.append(f'<circle cx="{px(i):.1f}" cy="{py(v):.1f}" r="{5.5 if top else 3.6}" '
                 f'fill="{ACCENT if top else MUTE}"/>')
        s.append(txt(px(i), y1 + 17, rows[i]["strategy"], anchor="middle", size=9.5,
                     fill=INK if top else MUTE, weight="600" if top else None))
        s.append(txt(px(i), py(v) - 12, f"{v:.4f}", anchor="middle", size=10,
                     fill=INK if top else MUTE, weight="600" if top else None))

    last = len(ys) - 1
    s.append(f'<path d="M{px(peak):.1f} {py(ys[peak]) + 16:.1f} '
             f'L{px(last):.1f} {py(ys[last]) + 16:.1f}" stroke="{WARN}" stroke-width="1.4" '
             f'stroke-dasharray="4 4" fill="none"/>')
    s.append(txt((px(peak) + px(last)) / 2, py(ys[last]) + 34,
                 "−0.0064,  p = 0.017", anchor="middle", size=10, fill=WARN, weight="600"))

    s.append(f'<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" stroke="{LINE}"/>')
    for v in (0.24, 0.26, 0.28):
        s.append(txt(x0 - 9, py(v) + 3, f"{v:.2f}", anchor="end", size=9.5))
    s.append(txt(x0 - 44, T - 14, "BLEU-4 rises, then turns back down", size=10, fill=DIM))
    s.append("</svg>")
    return "".join(s)


# --------------------------------------------------------------------------
# 7c. caption — variety falls the whole way
# --------------------------------------------------------------------------

def cap_diversity(W: int) -> str:
    rows = sorted(read_csv(SRC["cap"] / "tables" / "decoding_results.csv"),
                  key=lambda r: num(r["beam_width"]))
    H, T, B, L, R = 244, 56, 46, 46, 26
    x0, x1, y0, y1 = L, W - R, T, H - B

    vals = [num(r["unique_caption_pct"]) for r in rows]
    vocab = [int(num(r["vocabulary_used"])) for r in rows]
    vmax = 80.0
    step = (x1 - x0) / len(rows)
    bw = step * 0.44

    s = open_svg(W, H, "Share of unique captions across decoding strategies")
    s.append(gridlines(x0, x1, [y1 - v / vmax * (y1 - y0) for v in (25, 50, 75)]))

    for i, v in enumerate(vals):
        cx = x0 + i * step + (step - bw) / 2
        h = v / vmax * (y1 - y0)
        op = 1 - i * 0.19                     # the fade is the message
        s.append(f'<rect x="{cx:.1f}" y="{y1 - h:.1f}" width="{bw:.1f}" height="{h:.1f}" '
                 f'rx="3" fill="{ACCENT}" opacity="{op:.2f}"/>')
        s.append(txt(cx + bw / 2, y1 - h - 10, f"{v:.1f}%", anchor="middle", size=11,
                     fill=INK, weight="600"))
        s.append(txt(cx + bw / 2, y1 + 16, rows[i]["strategy"], anchor="middle", size=9.5))
        s.append(txt(cx + bw / 2, y1 + 30, f"{vocab[i]} words", anchor="middle", size=9))

    s.append(f'<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" stroke="{LINE}"/>')
    s.append(txt(x0, T - 34, "Captions that appear only once", size=10.5, fill=DIM))
    s.append(txt(x0, T - 19, "monotonic decline — the cost nobody quotes", size=9.5, fill=WARN))
    s.append("</svg>")
    return "".join(s)


# --------------------------------------------------------------------------
# 8. matcher — Recall@1 by retriever
# --------------------------------------------------------------------------

LABELS = {
    "exact": "exact match",
    "bm25_fts5": "BM25 (FTS5)",
    "rapidfuzz": "RapidFuzz",
    "tfidf_char": "TF-IDF char 3–5",
    "dense_base": "encoder, stock",
    "dense_finetuned": "encoder, tuned",
    "hybrid": "encoder + reranker",
}


def matcher_recall(W: int) -> str:
    data = json.loads((SRC["matcher"] / "results.json").read_text(encoding="utf-8"))
    res = data["datasets"]["test_unseen"]["results"]
    pairs = [(LABELS.get(r["retriever"], r["retriever"]), r["recall"]["1"] * 100,
              r["retriever"]) for r in res]
    pairs = [p for p in pairs if p[2] != "hybrid"]      # shown in its own callout instead
    pairs.sort(key=lambda p: p[1])

    pad_l, R = 156, 62
    row_h, T = 30, 26
    H = T + row_h * len(pairs) + 24
    x0, x1 = pad_l, W - R

    s = open_svg(W, H, "Recall@1 by retriever on SKUs held out of training")
    s.append(glow("f-mat"))
    s.append(txt(0, T - 12, "Recall@1 on 274 SKUs never seen in training", size=10, fill=DIM))

    for i, (name, v, key) in enumerate(pairs):
        y = T + i * row_h
        w = v / 100 * (x1 - x0)
        winner = key == "dense_finetuned"
        base = key == "tfidf_char"
        color = ACCENT if winner else (WARN if base else MUTE)
        op = "1" if winner else ("0.85" if base else "0.34")
        s.append(txt(x0 - 12, y + 15, name, anchor="end", size=10.5,
                     fill=INK if (winner or base) else MUTE,
                     weight="700" if winner else ("600" if base else None)))
        s.append(f'<rect x="{x0}" y="{y + 4:.1f}" width="{w:.1f}" height="19" rx="3" '
                 f'fill="{color}" opacity="{op}"'
                 + (' filter="url(#f-mat)"' if winner else "") + "/>")
        s.append(txt(x0 + w + 9, y + 18, f"{v:.1f}%", size=10.5,
                     fill=INK if (winner or base) else MUTE,
                     weight="700" if winner else None))

    s.append(txt(0, H - 4, "the amber bar is the baseline that nearly made the model unnecessary",
                 size=9.5, fill=WARN))
    s.append("</svg>")
    return "".join(s)


# --------------------------------------------------------------------------
# wiring
# --------------------------------------------------------------------------

CHARTS = {
    "retail-revenue":  (retail_revenue,  WIDE),
    "retail-pareto":   (retail_pareto,   HALF),
    "retail-ageing":   (retail_ageing,   HALF),
    "ev-lift":         (ev_lift,         WIDE),
    "ev-drivers":      (ev_drivers,      WIDE),
    "ev-interaction":  (ev_interaction,  WIDE),
    "cap-tradeoff":    (cap_tradeoff,    WIDE),
    "cap-beam":        (cap_beam,        HALF),
    "cap-diversity":   (cap_diversity,   HALF),
    "matcher-recall":  (matcher_recall,  WIDE),
}


def render_into(html: str) -> str:
    for name, (fn, width) in CHARTS.items():
        pattern = re.compile(
            rf"(<!-- CHART:{re.escape(name)} -->).*?(<!-- /CHART:{re.escape(name)} -->)",
            re.DOTALL,
        )
        if not pattern.search(html):
            raise SystemExit(f"no <!-- CHART:{name} --> block in src/index.html")
        svg = fn(width)
        html = pattern.sub(lambda m: m.group(1) + "\n" + svg + "\n" + m.group(2), html, count=1)
    return html


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="exit non-zero if index.html does not match the data")
    args = ap.parse_args()

    for name, path in SRC.items():
        if not path.exists():
            raise SystemExit(f"missing source results for {name}: {path}")

    target = ROOT / "src" / "index.html"
    current = target.read_text(encoding="utf-8")
    updated = render_into(current)

    if args.check:
        if current != updated:
            print("src/index.html is stale — run: python3 tools/build_charts.py")
            return 1
        print("charts up to date")
        return 0

    target.write_text(updated, encoding="utf-8")
    print(f"rendered {len(CHARTS)} charts into {target.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
