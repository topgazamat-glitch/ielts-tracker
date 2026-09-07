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


MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def short_key(key):
    """2026-W31 -> W31, 2026-09 -> Sep, 2026-09-05 -> 5 Sep."""
    if "W" in key:
        return key.split("-")[-1]
    bits = key.split("-")
    if len(bits) == 2:
        return MONTHS[int(bits[1]) - 1]
    if len(bits) == 3:
        return "%d %s" % (int(bits[2]), MONTHS[int(bits[1]) - 1])
    return key


def period_bars(rows, label="Progress over time"):
    """Two series per period: average score out of 10 and lesson mark out of 5."""
    if not rows:
        return _empty("Nothing recorded yet")
    n = len(rows)
    parts = [_grid()]
    slot = PLOT_W / max(n, 1)
    bw = min(38, slot * 0.34)
    for i, row in enumerate(rows):
        centre = PAD_L + slot * (i + 0.5)
        if row["score"] is not None:
            h = PH_of(row["score"])
            parts.append(
                f'<rect class="bar" x="{centre - bw - 2:.1f}" y="{_y(row["score"]):.1f}" '
                f'width="{bw:.1f}" height="{h:.1f}" rx="3">'
                f'<title>{escape(row["key"])}: {row["score"]}/10 from {row["count"]} piece(s)'
                f'</title></rect>')
        if row["mark"] is not None:
            scaled = row["mark"] * 2                    # 1-5 shown on the same 0-10 axis
            h = PH_of(scaled)
            parts.append(
                f'<rect class="bar2" x="{centre + 2:.1f}" y="{_y(scaled):.1f}" '
                f'width="{bw:.1f}" height="{h:.1f}" rx="3">'
                f'<title>{escape(row["key"])}: lesson mark {row["mark"]}/5</title></rect>')
        parts.append(
            f'<text class="ax" x="{centre:.1f}" y="{H - 12}" text-anchor="middle">'
            f'{escape(short_key(row["key"]))}</text>')
    parts.append(f'<line class="axis" x1="{PAD_L}" y1="{_y(0):.1f}" '
                 f'x2="{W - PAD_R}" y2="{_y(0):.1f}"/>')
    return (f'<svg class="chart" viewBox="0 0 {W} {H}" role="img" '
            f'aria-label="{escape(label)}">{"".join(parts)}</svg>')


def PH_of(value):
    return max(1.0, PLOT_H * value / 10.0)


def bars_h(rows, label="Standings"):
    """Horizontal 0-100 bars - the combined index per student."""
    if not rows:
        return _empty("No students yet")
    rows = rows[:20]
    height = 34 + 26 * len(rows) + 16
    left, right = 150, 46
    width = W - left - right
    parts = []
    for i, (name, value, flagged) in enumerate(rows):
        y = 18 + i * 26
        parts.append(f'<text class="rowlabel" x="6" y="{y + 11}">{escape(name[:20])}</text>')
        parts.append(f'<rect class="track" x="{left}" y="{y}" width="{width}" '
                     f'height="14" rx="4"/>')
        if value is not None:
            parts.append(f'<rect class="{"bar warn" if flagged else "bar"}" x="{left}" '
                         f'y="{y}" width="{max(3, width * value / 100):.1f}" height="14" rx="4"/>')
            parts.append(f'<text class="ax" x="{left + width + 8}" y="{y + 11}">{value}</text>')
    return (f'<svg class="chart" viewBox="0 0 {W} {height}" role="img" '
            f'aria-label="{escape(label)}">{"".join(parts)}</svg>')


def journey_chart(j, w=560, h=220):
    """Their own road: where they started, where they are going, and the real
    marked work in between.

    The two horizontal lines are the promises they made themselves. The line
    that wanders between them is their actual average, week by week, so the
    picture cannot flatter them.
    """
    pad_l, pad_r, pad_t, pad_b = 44, 16, 22, 30
    lo = min(j["start"], min(p["score"] for p in j["points"])) - 0.6
    hi = max(j["goal"], max(p["score"] for p in j["points"])) + 0.6
    lo, hi = max(0, lo), min(10, hi)
    if hi - lo < 1:
        hi = lo + 1

    def y(v):
        return pad_t + (hi - v) / (hi - lo) * (h - pad_t - pad_b)

    pts = j["points"]
    def x(i):
        if len(pts) == 1:
            return pad_l + (w - pad_l - pad_r) / 2
        return pad_l + i * (w - pad_l - pad_r) / (len(pts) - 1)

    out = [f'<svg class="chart" viewBox="0 0 {w} {h}" width="100%" '
           f'preserveAspectRatio="xMidYMid meet" role="img" '
           f'aria-label="Your progress from {j["start"]:g} towards {j["goal"]:g}">']

    # the band between start and goal - the ground they mean to cover
    out.append(f'<rect x="{pad_l}" y="{y(j["goal"]):.1f}" width="{w-pad_l-pad_r}" '
               f'height="{max(0, y(j["start"]) - y(j["goal"])):.1f}" '
               f'fill="var(--accent-soft)" opacity=".55"/>')
    for value, label, colour, dash in (
            (j["goal"], "goal %g" % j["goal"], "var(--ok)", "5 4"),
            (j["start"], "start %g" % j["start"], "var(--ink-3)", "3 4")):
        out.append(f'<line x1="{pad_l}" y1="{y(value):.1f}" x2="{w-pad_r}" '
                   f'y2="{y(value):.1f}" stroke="{colour}" stroke-width="1.5" '
                   f'stroke-dasharray="{dash}"/>')
        out.append(f'<text x="{pad_l-8}" y="{y(value)+4:.1f}" text-anchor="end" '
                   f'font-size="11" fill="{colour}">{label}</text>')

    line = " ".join("%.1f,%.1f" % (x(i), y(p["score"])) for i, p in enumerate(pts))
    if len(pts) > 1:
        out.append(f'<polyline points="{line}" fill="none" stroke="var(--accent)" '
                   f'stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>')
    ring = ' stroke="var(--surface)" stroke-width="2"'
    for i, p in enumerate(pts):
        last = i == len(pts) - 1
        out.append('<circle cx="%.1f" cy="%.1f" r="%d" fill="var(--accent)"%s/>'
                   % (x(i), y(p["score"]), 5 if last else 3, ring if last else ""))
    here = pts[-1]
    out.append(f'<text x="{x(len(pts)-1):.1f}" y="{y(here["score"])-12:.1f}" '
               f'text-anchor="middle" font-size="12" font-weight="700" '
               f'fill="var(--accent)">{here["score"]:g}</text>')
    out.append(f'<text x="{pad_l}" y="{h-8}" font-size="11" fill="var(--ink-3)">'
               f'{len(pts)} week{"" if len(pts) == 1 else "s"} of marked work</text>')
    out.append("</svg>")
    return "".join(out)


# The path up the mountain, as a series of points from the foot to the summit.
# Hand-placed rather than computed, so the slope eases off near the top the way
# a real ridge does instead of climbing in a straight line.
_RIDGE = [(52, 300), (118, 279), (178, 258), (238, 232), (292, 210),
          (344, 183), (396, 158), (444, 131), (490, 108), (532, 84),
          (566, 66), (596, 50), (614, 38)]


def _along(fraction):
    """A point some fraction of the way up the ridge."""
    fraction = max(0.0, min(1.0, fraction))
    spot = fraction * (len(_RIDGE) - 1)
    i = min(int(spot), len(_RIDGE) - 2)
    a, b = _RIDGE[i], _RIDGE[i + 1]
    t = spot - i
    return a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t


def mountain(c, w=640, h=340):
    """Their climb, drawn as a mountain with a camp for every stage.

    The climber sits where their marked work has actually carried them, so the
    picture moves a little every time a piece of homework is graded.
    """
    out = ['<svg class="climb" viewBox="0 0 %d %d" width="100%%" '
           'preserveAspectRatio="xMidYMid meet" role="img" aria-label="Climb from '
           '%s to %s, %d%% of the way">'
           % (w, h, c["labels"][0], c["labels"][-1], c["percent"])]
    out.append(
        '<defs>'
        '<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0%" stop-color="var(--accent-soft)"/>'
        '<stop offset="100%" stop-color="var(--surface)"/></linearGradient>'
        '<linearGradient id="rock" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0%" stop-color="var(--accent)" stop-opacity=".85"/>'
        '<stop offset="100%" stop-color="var(--accent)" stop-opacity=".45"/>'
        '</linearGradient></defs>')
    out.append('<rect width="%d" height="%d" fill="url(#sky)" rx="12"/>' % (w, h))

    # a softer ridge behind, for depth
    out.append('<path d="M0 %d L 150 %d L 250 %d L 360 %d L 470 %d L %d %d Z" '
               'fill="var(--accent)" opacity=".13"/>' % (h, 210, 245, 175, 205, w, h))
    # the mountain they are on
    ridge = " ".join("L %d %d" % p for p in _RIDGE)
    out.append('<path d="M 20 %d %s L %d %d Z" fill="url(#rock)"/>'
               % (h - 20, ridge, w - 12, h - 20))
    # snow on the summit
    out.append('<path d="M %d %d L %d %d L %d %d L %d %d Z" fill="#ffffff" '
               'opacity=".75"/>' % (566, 66, 596, 50, 614, 38, 600, 82))

    # the path itself
    out.append('<polyline points="%s" fill="none" stroke="var(--surface)" '
               'stroke-width="2" stroke-dasharray="4 5" opacity=".7"/>'
               % " ".join("%d,%d" % p for p in _RIDGE))

    n = c["camps"]
    reached = int(c["climbed"])
    # A long climb has more camps than there is room for names. Name the ones
    # that mean something - where they began, where they are, what is next and
    # where they are going - and leave the rest as marks on the path.
    named = {0, n, reached, min(reached + 1, n)}
    if n <= 6:
        named = set(range(n + 1))
    for i, label in enumerate(c["labels"]):
        x, y = _along(i / float(n)) if n else _along(0)
        passed = i <= reached
        fill = "var(--accent)" if passed else "var(--surface)"
        out.append('<circle cx="%.1f" cy="%.1f" r="%d" fill="%s" '
                   'stroke="var(--accent)" stroke-width="2"/>'
                   % (x, y, 5 if i in named else 3.5, fill))
        if i not in named:
            continue
        up = (i % 2 == 0)
        anchor = "middle"
        if i == 0:
            anchor = "start"
        elif i == n:
            anchor = "end"
        out.append('<text x="%.1f" y="%.1f" text-anchor="%s" font-size="10.5" '
                   'font-weight="%s" fill="var(--ink-2)">%s</text>'
                   % (x, y - 13 if up else y + 21, anchor,
                      "700" if passed else "500", label))

    cx, cy = _along(c["climbed"] / float(n)) if n else _along(0)
    out.append('<text x="%.1f" y="%.1f" font-size="26" text-anchor="middle">'
               '\U0001F9D7</text>' % (cx, cy - 6))
    fx, fy = _along(1.0)
    out.append('<text x="%.1f" y="%.1f" font-size="20" text-anchor="middle">'
               '\U0001F6A9</text>' % (fx + 10, fy - 10))
    out.append("</svg>")
    return "".join(out)
