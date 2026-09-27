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
# The mountain. The route the camps sit on rises from the left foot to the
# summit at the right; the ridges behind it are only scenery. Everything is
# drawn in the hero's own dark world - deep brand at the top, brand at the
# horizon, white and gold on it - so it holds in light and dark mode alike.
_ROUTE = [(46, 236), (96, 224), (146, 214), (196, 198), (244, 184), (290, 166),
          (334, 150), (376, 132), (416, 116), (452, 100), (486, 84), (518, 66),
          (548, 48)]
_RIDGE_NEAR = ("M 0 300 L 0 262 L 40 244 L 100 232 L 150 220 L 200 204 L 250 188 "
               "L 300 170 L 340 152 L 380 134 L 420 118 L 458 100 L 492 82 L 522 64 "
               "L 548 44 L 566 60 L 590 90 L 620 130 L 640 150 L 640 300 Z")
_RIDGE_MID = ("M 0 300 L 0 230 L 60 210 L 120 224 L 170 200 L 230 214 L 280 186 "
              "L 330 200 L 380 176 L 430 190 L 470 160 L 520 178 L 570 140 L 610 168 "
              "L 640 152 L 640 300 Z")
_RIDGE_FAR = ("M 0 300 L 0 200 L 50 176 L 110 196 L 160 170 L 220 188 L 270 156 "
              "L 320 174 L 370 146 L 420 164 L 460 136 L 500 150 L 550 118 L 600 146 "
              "L 640 126 L 640 300 Z")
_SNOW = "M 522 64 L 548 44 L 566 60 L 578 76 L 560 70 L 548 80 L 534 72 Z"
_STARS = [(38, 30), (90, 52), (140, 22), (210, 44), (260, 18), (330, 38), (392, 24),
          (446, 40), (500, 16), (598, 32), (622, 58), (176, 70), (300, 66), (476, 56)]


def _along(fraction):
    """A point some fraction of the way up the route."""
    fraction = max(0.0, min(1.0, fraction))
    spot = fraction * (len(_ROUTE) - 1)
    i = min(int(spot), len(_ROUTE) - 2)
    a, b = _ROUTE[i], _ROUTE[i + 1]
    t = spot - i
    return a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t


def mountain(c, w=640, h=300):
    """Their climb, drawn as a mountain at night with a camp for every stage.

    The climber sits where their marked work has actually carried them, so the
    picture moves a little every time a piece of homework is graded. Passed
    camps are lit; the one ahead is ringed; the summit carries the flag. Only
    the camps that mean something are named on the picture - the route list
    under it names them all.
    """
    if c is None:
        n, climbed, labels = 4, 0.0, []
    else:
        n, climbed, labels = c["camps"], c["climbed"], c["labels"]
    reached = int(climbed)
    out = ['<svg class="climb" viewBox="0 0 %d %d" width="100%%" '
           'preserveAspectRatio="xMidYMid slice" role="img" aria-label="%s">'
           % (w, h, ("Climb from %s to %s, %d%% of the way"
                     % (labels[0], labels[-1], c["percent"])) if c else "The mountain")]
    out.append(
        '<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0%" stop-color="var(--brand-deep)"/>'
        '<stop offset="100%" stop-color="var(--brand)"/></linearGradient>'
        '<radialGradient id="glow" cx="50%" cy="50%" r="50%">'
        '<stop offset="0%" stop-color="#fff" stop-opacity=".9"/>'
        '<stop offset="100%" stop-color="#fff" stop-opacity="0"/></radialGradient></defs>')
    out.append('<rect width="%d" height="%d" fill="url(#sky)"/>' % (w, h))
    for x, y in _STARS:
        out.append('<circle cx="%d" cy="%d" r="%s" fill="#fff" opacity="%s"/>'
                   % (x, y, "1.3" if (x + y) % 3 else "1.8", ".55" if (x + y) % 2 else ".35"))
    out.append('<path d="%s" fill="#fff" opacity=".08"/>' % _RIDGE_FAR)
    out.append('<path d="%s" fill="#fff" opacity=".13"/>' % _RIDGE_MID)
    out.append('<path d="%s" fill="#fff" opacity=".22"/>' % _RIDGE_NEAR)
    out.append('<path d="%s" fill="#fff" opacity=".85"/>' % _SNOW)
    # the route: the stretch already walked is solid, the rest is dashed
    pts = " ".join("%d,%d" % p for p in _ROUTE)
    out.append('<polyline points="%s" fill="none" stroke="#fff" stroke-width="2" '
               'stroke-dasharray="3 6" stroke-linecap="round" opacity=".55"/>' % pts)
    if c and climbed > 0:
        walked = [_along(k / 40.0 * climbed / n) for k in range(41)]
        out.append('<polyline points="%s" fill="none" stroke="#fff" stroke-width="3" '
                   'stroke-linecap="round" stroke-linejoin="round" opacity=".95"/>'
                   % " ".join("%.1f,%.1f" % p for p in walked))
    # the summit flag
    fx, fy = _along(1.0)
    out.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#fff" '
               'stroke-width="2" stroke-linecap="round"/>' % (fx, fy, fx, fy - 30))
    out.append('<path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f Z" fill="var(--gold)"/>'
               % (fx + 1, fy - 30, fx + 24, fy - 23, fx + 1, fy - 15))
    if not c:
        out.append("</svg>")
        return "".join(out)
    # the camps
    named = {0, n, reached, min(reached + 1, n)} if n > 5 else set(range(n + 1))
    for i, label in enumerate(labels):
        x, y = _along(i / float(n))
        passed = i <= reached
        nxt = i == min(reached + 1, n) and i != reached
        if passed:
            out.append('<circle cx="%.1f" cy="%.1f" r="5.5" fill="#fff"/>' % (x, y))
        elif nxt:
            out.append('<circle cx="%.1f" cy="%.1f" r="6" fill="var(--brand)" '
                       'stroke="var(--gold)" stroke-width="2.5"/>' % (x, y))
        else:
            out.append('<circle cx="%.1f" cy="%.1f" r="4" fill="var(--brand)" '
                       'stroke="#fff" stroke-width="1.5" opacity=".8"/>' % (x, y))
        if i not in named or i == reached:
            continue           # the reached camp is named by the climber's tag
        anchor = "start" if i == 0 else "end" if i == n else "middle"
        dy, dx = (24 if i % 2 == 0 else -14), (6 if i == 0 else 0)
        if i == n:
            dy, dx, anchor = 4, -12, "end"       # left of the summit, on the sky
        out.append('<text x="%.1f" y="%.1f" text-anchor="%s" font-size="12" '
                   'font-weight="%s" fill="#fff" fill-opacity="%s">%s</text>'
                   % (x + dx, y + dy, anchor,
                      "700" if (passed or nxt) else "500", ".95" if (passed or nxt) else ".7",
                      label))
    # the climber: a lit marker where their work has carried them, with a tag
    cx, cy = _along(climbed / float(n))
    out.append('<circle cx="%.1f" cy="%.1f" r="26" fill="url(#glow)" opacity=".45"/>' % (cx, cy))
    out.append('<circle class="pulse" cx="%.1f" cy="%.1f" r="12" fill="none" '
               'stroke="#fff" stroke-width="1.5" opacity=".6"/>' % (cx, cy))
    out.append('<circle cx="%.1f" cy="%.1f" r="8" fill="var(--gold)" stroke="#fff" '
               'stroke-width="2.5"/>' % (cx, cy))
    tag = "You"
    tw = 8 * len(tag) + 18
    tx = cx - tw / 2.0
    ty = cy - 44
    if tx < 8:
        tx = 8
    if tx + tw > w - 8:
        tx = w - 8 - tw
    out.append('<rect x="%.1f" y="%.1f" width="%d" height="22" rx="11" fill="#fff"/>'
               % (tx, ty, tw))
    out.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="12" '
               'font-weight="700" fill="var(--brand-deep)">%s</text>'
               % (tx + tw / 2.0, ty + 15, tag))
    out.append('<path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f Z" fill="#fff"/>'
               % (cx - 5, ty + 22, cx + 5, ty + 22, cx, ty + 29))
    out.append("</svg>")
    return "".join(out)
