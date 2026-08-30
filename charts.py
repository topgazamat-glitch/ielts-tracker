"""Hand-rolled SVG charts - no chart library, no CDN, works offline."""
from html import escape

W, H = 720, 240
PAD_L, PAD_R, PAD_T, PAD_B = 34, 12, 14, 34
PLOT_W = W - PAD_L - PAD_R
PLOT_H = H - PAD_T - PAD_B
SCALE_MIN, SCALE_MAX = 0.0, 10.0


def _y(v):
    frac = (v - SCALE_MIN) / (SCALE_MAX - SCALE_MIN)
    return PAD_T + PLOT_H * (1 - frac)


def _x(i, n):
    if n <= 1:
        return PAD_L + PLOT_W / 2
    return PAD_L + PLOT_W * i / (n - 1)


def _grid():
    parts = []
    for v in (0, 2, 4, 6, 8, 10):
        y = _y(v)
        parts.append(
            f'<line class="grid" x1="{PAD_L}" y1="{y:.1f}" x2="{W-PAD_R}" y2="{y:.1f}"/>'
        )
        parts.append(f'<text class="ax" x="{PAD_L-8}" y="{y+4:.1f}" text-anchor="end">{v}</text>')
    return "".join(parts)


def _empty(msg="No data yet"):
    return (
        f'<svg class="chart" viewBox="0 0 {W} {H}" role="img" aria-label="{escape(msg)}">'
        f'<text class="empty" x="{W/2}" y="{H/2}" text-anchor="middle">{escape(msg)}</text></svg>'
    )


def score_line(timeline, band=None, label="Score trend"):
    """Rolling-3 line with raw score dots; misses drawn as gaps, never as zero.

    `band` is an optional list of group averages aligned to the same points.
    """
    if not timeline:
        return _empty()
    n = len(timeline)
    scores = [t["score"] for t in timeline]
    from core import rolling_average

    roll = rolling_average(scores)
    parts = [_grid()]

    # group-average reference line, drawn behind the student's own line
    if band:
        pts = [(i, v) for i, v in enumerate(band) if v is not None]
        if len(pts) > 1:
            d = " ".join(f"{_x(i,n):.1f},{_y(v):.1f}" for i, v in pts)
            parts.append(f'<polyline class="band" points="{d}"/>')

    # the rolling line breaks into segments so a miss leaves a visible gap
    # The trend line spans the graded points and bridges across misses - a
    # student with scattered gaps still gets a readable line, and the misses
    # stay visible as their own markers along the axis below.
    graded_pts = [(i, v) for i, v in enumerate(roll) if v is not None]
    if len(graded_pts) > 1:
        d = " ".join(f"{_x(i,n):.1f},{_y(v):.1f}" for i, v in graded_pts)
        parts.append(f'<polyline class="line" points="{d}"/>')

    for i, t in enumerate(timeline):
        x = _x(i, n)
        title = escape(f'{t["title"]}: ')
        if t["score"] is not None:
            parts.append(
                f'<circle class="dot" cx="{x:.1f}" cy="{_y(t["score"]):.1f}" r="4">'
                f"<title>{title}{t['score']}</title></circle>"
            )
        elif t["status"] == "missing":
            y = H - PAD_B
            parts.append(
                f'<path class="miss" d="M{x-4:.1f},{y-4} l8,8 M{x+4:.1f},{y-4} l-8,8">'
                f"<title>{title}not submitted</title></path>"
            )
        else:
            parts.append(
                f'<circle class="pending" cx="{x:.1f}" cy="{H-PAD_B-4}" r="3">'
                f"<title>{title}awaiting grading</title></circle>"
            )

    parts.append(
        f'<line class="axis" x1="{PAD_L}" y1="{H-PAD_B}" x2="{W-PAD_R}" y2="{H-PAD_B}"/>'
    )
    if n > 1:
        parts.append(_tick(timeline[0]["title"], PAD_L, "start"))
        parts.append(_tick(timeline[-1]["title"], W - PAD_R, "end"))
    return (
        f'<svg class="chart" viewBox="0 0 {W} {H}" role="img" '
        f'aria-label="{escape(label)}">{"".join(parts)}</svg>'
    )


def _tick(text, x, anchor):
    t = escape(text[:24])
    return f'<text class="ax" x="{x}" y="{H-8}" text-anchor="{anchor}">{t}</text>'


def distribution(scores, label="Score distribution"):
    """Count of scores in each 1-10 bucket for a single assignment."""
    if not scores:
        return _empty("Nothing graded yet")
    buckets = [0] * 11
    for s in scores:
        buckets[max(0, min(10, int(round(s))))] += 1
    peak = max(buckets) or 1
    bw = PLOT_W / 10.5
    parts = []
    for v in range(1, 11):
        c = buckets[v]
        h = PLOT_H * c / peak
        x = PAD_L + (v - 1) * bw
        y = PAD_T + PLOT_H - h
        parts.append(
            f'<rect class="bar" x="{x:.1f}" y="{y:.1f}" width="{bw-6:.1f}" '
            f'height="{h:.1f}" rx="3"><title>{v}/10: {c} student(s)</title></rect>'
        )
        parts.append(
            f'<text class="ax" x="{x+(bw-6)/2:.1f}" y="{H-12}" text-anchor="middle">{v}</text>'
        )
        if c:
            parts.append(
                f'<text class="barval" x="{x+(bw-6)/2:.1f}" y="{y-4:.1f}" '
                f'text-anchor="middle">{c}</text>'
            )
    parts.append(
        f'<line class="axis" x1="{PAD_L}" y1="{PAD_T+PLOT_H}" x2="{W-PAD_R}" '
        f'y2="{PAD_T+PLOT_H}"/>'
    )
    return (
        f'<svg class="chart" viewBox="0 0 {W} {H}" role="img" '
        f'aria-label="{escape(label)}">{"".join(parts)}</svg>'
    )


def sparkline(scores, w=110, h=26):
    """Tiny inline trend for roster tables."""
    vals = [s for s in scores if s is not None]
    if len(vals) < 2:
        return f'<svg class="spark" viewBox="0 0 {w} {h}"></svg>'
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1
    pts = " ".join(
        f"{2 + (w-4)*i/(len(vals)-1):.1f},{2 + (h-4)*(1-(v-lo)/span):.1f}"
        for i, v in enumerate(vals)
    )
    cls = "up" if vals[-1] >= vals[0] else "down"
    return (
        f'<svg class="spark {cls}" viewBox="0 0 {w} {h}" aria-hidden="true">'
        f'<polyline points="{pts}"/></svg>'
    )
