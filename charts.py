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
# ------------------------------------------------------------ the mountain
#
# The mountain is drawn the way light falls on a real one at dawn: the
# ridges are jagged rather than ruled, the faces turned towards the first
# light are lit rose and the ones turned away are in shadow, the snow runs
# down into the gullies and catches the light on the same side as the rock,
# the rock has grain, the ranges behind go pale into the haze, and the pines
# at the foot are black against it. All of it comes from a fixed seed, so
# the mountain is the same one every time and for every student; only the
# route, the camps and the climber change.

def _frac(points, rough, depth, seed):
    """A line through `points`, broken into a natural edge: every segment is
    split at its middle, and the middle pushed sideways by up to `rough` of
    its length, over and over. The same seed makes the same edge."""
    import math
    import random
    rnd = random.Random(seed)
    pts = [tuple(map(float, p)) for p in points]
    for _level in range(depth):
        out = [pts[0]]
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            dx, dy = x2 - x1, y2 - y1
            span = math.hypot(dx, dy) or 1.0
            push = rnd.uniform(-1.0, 1.0) * span * rough
            out.append(((x1 + x2) / 2.0 - dy / span * push, (y1 + y2) / 2.0 + dx / span * push))
            out.append((x2, y2))
        pts = out
        rough *= 0.62
    return pts


def _route_y(x):
    """How high the route is at x, for keeping the crest above it."""
    for (x1, y1), (x2, y2) in zip(_ROUTE, _ROUTE[1:]):
        if x1 <= x <= x2:
            return y1 + (y2 - y1) * (x - x1) / float(x2 - x1)
    return None


def _d(points, close=False):
    return "M " + " L ".join("%.1f %.1f" % p for p in points) + (" Z" if close else "")


def _between(points, lo, hi):
    return [p for p in points if lo <= p[0] <= hi]


def _blob(cx, cy, r, seed):
    """A small patch of snow: a ragged ring around a point."""
    import math
    ring = [(cx + r * math.cos(t * math.pi / 3) * (1.4 if t % 3 == 0 else 1.0),
             cy + r * 0.6 * math.sin(t * math.pi / 3)) for t in range(7)]
    return _frac(ring, 0.22, 3, seed)


def _build_mountain():
    # the crest of the main mountain, left foot to right edge; the route runs
    # across its face, so the crest is kept above the route all the way up
    crest = _frac([(0, 250), (60, 218), (130, 194), (180, 188), (240, 160), (300, 128),
                   (340, 138), (400, 104), (450, 84), (500, 60), (549, 36), (566, 55),
                   (585, 70), (604, 60), (625, 90), (640, 104)], 0.07, 4, 11)
    fixed = []
    for x, y in crest:
        ry = _route_y(x)
        if ry is not None and x < 549:
            y = min(y, ry - 9)                 # the route is on the face, never in the sky
        fixed.append((x, y))
    crest = fixed
    summit = min(crest, key=lambda p: p[1])
    massif = crest + [(640, 300), (0, 300)]

    def on_crest(x):
        return min(crest, key=lambda p: abs(p[0] - x))

    def wedge(x_top, x_right, bottom, seed, rough=0.1):
        """A rib of the mountain: from the crest between two points, down to
        one point below - the shape a spur and the gully beside it make."""
        tl, tr = on_crest(x_top), on_crest(x_right)
        edge = _between(crest, tl[0], tr[0]) or [tl, tr]
        right_side = _frac([tr, bottom], rough, 4, seed)
        left_side = _frac([bottom, tl], rough, 4, seed + 1)
        return edge + right_side[1:] + left_side[1:]

    # the big face turned to the dawn: right of the spine from the summit
    spine = _frac([summit, (532, 84), (508, 132), (480, 192), (462, 250), (452, 300)], 0.09, 4, 21)
    right = [p for p in crest if p[0] >= summit[0]]
    lit_main = right + [(640, 300)] + list(reversed(spine))
    # ribs on the long left slope, each lit on its dawn side, leaning away
    ribs = [wedge(x, x + w, (x - 14 + dx, on_crest(x)[1] + h), 31 + k)
            for k, (x, w, h, dx) in enumerate((
                (62, 34, 70, 0), (128, 40, 84, 4), (206, 36, 92, -2), (286, 44, 104, 2),
                (356, 38, 112, 0), (410, 40, 118, 6), (462, 34, 110, 4)))]
    # on the lit face, the gullies are the shadows
    gullies = [wedge(x, x + w, bottom, 61 + k, 0.12) for k, (x, w, bottom) in enumerate((
        (566, 16, (552, 156)), (604, 18, (590, 176)), (625, 12, (618, 196)), (586, 10, (574, 132))))]

    # the snow: a ragged snowline, deeper in the gullies, and loose patches below
    # snow lies thick on the lit side and thin on the steep shadow side, and
    # its edge is torn by the rock, not scalloped
    cap_top = _between(crest, 494, 630)
    lower = _frac([(cap_top[-1][0], cap_top[-1][1] + 5), (617, 102), (609, 96), (603, 121),
                   (596, 104), (589, 110), (583, 131), (577, 108), (569, 114), (563, 124),
                   (556, 101), (549, 92), (542, 99), (534, 84), (526, 90), (517, 76),
                   (508, 80), (500, 69), (cap_top[0][0], cap_top[0][1] + 3)],
                  0.3, 5, 51)
    snow = cap_top + lower
    patches = []
    rim = _between(crest, 420, 632)

    # the ranges behind, paler as they go back
    far = _frac([(0, 182), (70, 160), (130, 176), (190, 142), (250, 166), (310, 132),
                 (380, 150), (440, 120), (520, 138), (590, 112), (640, 124)], 0.09, 5, 91)
    mid = _frac([(0, 214), (50, 196), (110, 210), (170, 180), (230, 204), (280, 186),
                 (350, 206), (420, 178), (500, 196), (570, 164), (640, 176)], 0.08, 5, 101)

    # the foot: a dark band of ground with pines against the haze
    ground = _frac([(0, 272), (60, 266), (120, 278), (200, 284), (300, 286), (400, 288),
                    (480, 282), (560, 272), (640, 266)], 0.05, 3, 111)
    pines = []
    import random
    rnd = random.Random(121)
    for lo, hi in ((0, 118), (500, 640)):
        x = lo + rnd.uniform(2, 8)
        while x < hi:
            base = min(ground, key=lambda p: abs(p[0] - x))[1] + 3
            h = rnd.uniform(14, 30) * (1.0 if (x < 60 or x > 580) else 0.72)
            wdt = h * rnd.uniform(0.34, 0.42)
            tiers = []
            for t in range(3):                 # three tiers of branches, narrowing up
                top = base - h * (1.0 - t * 0.28)
                half = wdt * (0.5 + t * 0.25) / 2.0
                foot = base - h * (0.55 - t * 0.24)
                tiers.append("M %.1f %.1f L %.1f %.1f L %.1f %.1f Z"
                             % (x, top, x + half, foot, x - half, foot))
            pines.append(" ".join(tiers) + " M %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f Z"
                         % (x - .9, base, x - .9, base - h * .3, x + .9, base - h * .3, x + .9, base))
            x += rnd.uniform(7, 15)
    return {
        "massif": _d(massif, True), "lit": _d(lit_main, True),
        "ribs": [_d(r, True) for r in ribs], "gullies": [_d(g, True) for g in gullies],
        "snow": _d(snow, True), "patches": [_d(pt, True) for pt in patches],
        "rim": _d(rim), "far": _d(far + [(640, 300), (0, 300)], True),
        "far_edge": _d(far), "mid": _d(mid + [(640, 300), (0, 300)], True),
        "ground": _d(ground + [(640, 300), (0, 300)], True), "pines": " ".join(pines),
        "summit": summit,
    }


_MOUNTAIN = _build_mountain()
# A few bright stars in the mountain's own sky; the faint ones are a CSS
# layer over the whole hero, so the sky runs on above the picture.
_BRIGHT = [(318, 34, 5, "tw1"), (404, 70, 4, "tw2"), (468, 26, 6, "tw3"),
           (612, 22, 4, "tw1"), (250, 88, 3, "tw2"), (150, 60, 4, "tw3")]


def _along(fraction):
    """A point some fraction of the way up the route."""
    fraction = max(0.0, min(1.0, fraction))
    spot = fraction * (len(_ROUTE) - 1)
    i = min(int(spot), len(_ROUTE) - 2)
    a, b = _ROUTE[i], _ROUTE[i + 1]
    t = spot - i
    return a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t


def _sparkle(x, y, r, cls):
    """A four-pointed twinkle: curves pulled into the centre."""
    return ('<path class="%s" d="M %.1f %.1f Q %.1f %.1f %.1f %.1f Q %.1f %.1f %.1f %.1f '
            'Q %.1f %.1f %.1f %.1f Q %.1f %.1f %.1f %.1f Z" fill="var(--dream-star)"/>'
            % (cls, x, y - r, x, y, x + r, y, x, y, x, y + r, x, y, x - r, y, x, y, x, y - r))


def mountain(c, w=640, h=300, avatar="", photo=""):
    """Their climb, drawn as a mountain at night with the summit catching
    the first light - the dream, lit, and the route to it.

    The sky is transparent: the hero behind the picture carries the night
    and the faint stars, so it runs on unbroken above it. The climber is the
    student's own face or animal, standing where their marked work has
    actually carried them; the stretch they have walked glows gold.
    """
    if c is None:
        n, climbed, labels = 4, 0.0, []
    else:
        n, climbed, labels = c["camps"], c["climbed"], c["labels"]
    reached = int(climbed)
    f = (climbed / float(n)) if (c and n) else 0.0
    cx, cy = _along(f)
    label = ("Climb from %s to %s, %d%% of the way" % (labels[0], labels[-1], c["percent"])
             if c else "A mountain at night, waiting for a route")
    out = ['<svg class="climb" viewBox="0 0 %d %d" width="100%%" '
           'preserveAspectRatio="xMidYMid meet" role="img" aria-label="%s">' % (w, h, label)]
    out.append(
        '<defs>'
        '<radialGradient id="cl-dawn"><stop offset="0%" stop-color="var(--dream-dawn)" stop-opacity=".75"/>'
        '<stop offset="45%" stop-color="var(--dream-rose)" stop-opacity=".28"/>'
        '<stop offset="100%" stop-color="var(--dream-rose)" stop-opacity="0"/></radialGradient>'
        '<radialGradient id="cl-halo"><stop offset="0%" stop-color="var(--dream-gold)" stop-opacity=".75"/>'
        '<stop offset="100%" stop-color="var(--dream-gold)" stop-opacity="0"/></radialGradient>'
        '<linearGradient id="cl-walk" gradientUnits="userSpaceOnUse" x1="46" y1="236" x2="548" y2="48">'
        '<stop offset="0%" stop-color="var(--dream-gold)"/>'
        '<stop offset="100%" stop-color="var(--dream-rose)"/></linearGradient>'
        '<filter id="cl-glow" x="-20%" y="-20%" width="140%" height="140%">'
        '<feGaussianBlur stdDeviation="3" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
        '<filter id="cl-mist" x="-30%" y="-200%" width="160%" height="500%">'
        '<feGaussianBlur stdDeviation="9"/></filter>'
        # the rock's grain: noise, lit from the dawn side, laid over the faces
        '<filter id="cl-grain" x="0" y="0" width="100%" height="100%">'
        '<feTurbulence type="fractalNoise" baseFrequency="0.05 0.014" numOctaves="3" seed="7"/>'
        '<feDiffuseLighting surfaceScale="4" lighting-color="#fff">'
        '<feDistantLight azimuth="330" elevation="38"/></feDiffuseLighting></filter>'
        '<linearGradient id="cl-far" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0%" stop-color="var(--dream-haze)"/>'
        '<stop offset="100%" stop-color="var(--dream-far)"/></linearGradient>'
        '<linearGradient id="cl-mid" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0%" stop-color="var(--dream-far)"/>'
        '<stop offset="100%" stop-color="var(--dream-mid)"/></linearGradient>'
        '<linearGradient id="cl-shade" gradientUnits="userSpaceOnUse" x1="0" y1="36" x2="0" y2="300">'
        '<stop offset="0%" stop-color="var(--dream-mid)"/>'
        '<stop offset="100%" stop-color="var(--dream-rock-shade)"/></linearGradient>'
        '<linearGradient id="cl-lit" gradientUnits="userSpaceOnUse" x1="0" y1="36" x2="0" y2="290">'
        '<stop offset="0%" stop-color="var(--dream-rock-glow)"/>'
        '<stop offset="28%" stop-color="var(--dream-rock-lit)"/>'
        '<stop offset="72%" stop-color="var(--dream-rock-lit)" stop-opacity=".35"/>'
        '<stop offset="100%" stop-color="var(--dream-rock-lit)" stop-opacity="0"/></linearGradient>'
        '<linearGradient id="cl-gully" gradientUnits="userSpaceOnUse" x1="0" y1="50" x2="0" y2="200">'
        '<stop offset="0%" stop-color="var(--dream-rock-shade)" stop-opacity=".85"/>'
        '<stop offset="100%" stop-color="var(--dream-rock-shade)" stop-opacity="0"/></linearGradient>'
        '<linearGradient id="cl-snowshade" gradientUnits="userSpaceOnUse" x1="0" y1="36" x2="0" y2="130">'
        '<stop offset="0%" stop-color="var(--dream-snow-shade)"/>'
        '<stop offset="100%" stop-color="var(--dream-snow-shade)" stop-opacity=".75"/></linearGradient>'
        '<linearGradient id="cl-haze" x1="0" y1="1" x2="0" y2="0">'
        '<stop offset="0%" stop-color="var(--dream-haze)" stop-opacity=".45"/>'
        '<stop offset="100%" stop-color="var(--dream-haze)" stop-opacity="0"/></linearGradient>'
        '<linearGradient id="cl-snowlit" gradientUnits="userSpaceOnUse" x1="0" y1="36" x2="0" y2="130">'
        '<stop offset="0%" stop-color="#fff"/>'
        '<stop offset="100%" stop-color="var(--dream-snow)"/></linearGradient>'
        '<linearGradient id="cl-rim" gradientUnits="userSpaceOnUse" x1="420" y1="0" x2="632" y2="0">'
        '<stop offset="0%" stop-color="var(--dream-rose)" stop-opacity="0"/>'
        '<stop offset="55%" stop-color="var(--dream-gold)"/>'
        '<stop offset="100%" stop-color="var(--dream-rose)" stop-opacity=".4"/></linearGradient>'
        + '<clipPath id="cl-massif"><path d="%s"/></clipPath>' % _MOUNTAIN["massif"]
        + '<clipPath id="cl-lightside"><path d="%s"/></clipPath>' % _MOUNTAIN["lit"]
        + '<clipPath id="cl-darkside"><path d="%s"/></clipPath>' % _MOUNTAIN["massif"]
        + '<clipPath id="cl-face"><circle cx="%.1f" cy="%.1f" r="13"/></clipPath>' % (cx, cy)
        + '</defs>')
    # the first light, behind the summit: the dream, glowing
    out.append('<ellipse class="breathe" cx="560" cy="112" rx="260" ry="112" fill="url(#cl-dawn)"/>')
    for x, y, r, cls in _BRIGHT:
        out.append(_sparkle(x, y, r, cls))
    m = _MOUNTAIN
    # the ranges behind: pale in the haze, the farthest catching the dawn
    out.append('<path d="%s" fill="url(#cl-far)"/>' % m["far"])
    out.append('<path d="%s" fill="none" stroke="var(--dream-rose)" stroke-width="1" '
               'opacity=".35"/>' % m["far_edge"])
    out.append('<ellipse class="mist" cx="200" cy="206" rx="190" ry="14" fill="#fff" '
               'opacity=".12" filter="url(#cl-mist)"/>')
    out.append('<path d="%s" fill="url(#cl-mid)"/>' % m["mid"])
    # the mountain: the whole of it in shadow, then the faces the light reaches,
    # fading into the haze of the valley rather than stopping at an edge
    out.append('<path d="%s" fill="url(#cl-shade)"/>' % m["massif"])
    out.append('<path d="%s" fill="url(#cl-lit)"/>' % m["lit"])
    for rib in m["ribs"]:
        out.append('<path d="%s" fill="url(#cl-lit)" opacity=".7"/>' % rib)
    for gully in m["gullies"]:
        out.append('<path d="%s" fill="url(#cl-gully)"/>' % gully)
    # the grain of the rock, over all of it
    out.append('<g class="rock" clip-path="url(#cl-massif)"><rect x="0" y="30" width="%d" '
               'height="270" fill="#fff" filter="url(#cl-grain)"/></g>' % w)
    # the snow: lavender in the shadow, rose-white where the light falls
    out.append('<path d="%s" fill="url(#cl-snowshade)"/>' % m["snow"])
    out.append('<g clip-path="url(#cl-lightside)"><path d="%s" fill="url(#cl-snowlit)"/>'
               % m["snow"] + "".join('<path d="%s" fill="var(--dream-snow)" opacity=".8"/>' % pt
                                     for pt in m["patches"]) + '</g>')
    out.append('<g clip-path="url(#cl-darkside)">' + "".join(
        '<path d="%s" fill="var(--dream-snow-shade)" opacity=".55"/>' % pt
        for pt in m["patches"]) + '</g>')
    # the first light running along the edge of the ridge
    out.append('<path d="%s" fill="none" stroke="url(#cl-rim)" stroke-width="1.6" '
               'stroke-linejoin="round" opacity=".9" filter="url(#cl-glow)"/>' % m["rim"])
    # the valley haze, rising over the foot of the mountain
    out.append('<rect x="0" y="170" width="%d" height="130" fill="url(#cl-haze)"/>' % w)
    out.append('<ellipse class="mist two" cx="330" cy="250" rx="260" ry="12" fill="#fff" '
               'opacity=".08" filter="url(#cl-mist)"/>')
    # the foot, and its pines, black against the haze
    out.append('<path d="%s" fill="var(--dream-pine)"/>' % m["ground"])
    out.append('<path d="%s" fill="var(--dream-pine)"/>' % m["pines"])
    # the whole route, faint; then the part already walked, drawn in gold
    out.append('<polyline points="%s" fill="none" stroke="#fff" stroke-width="2" '
               'stroke-dasharray="2 7" stroke-linecap="round" opacity=".45"/>'
               % " ".join("%d,%d" % p for p in _ROUTE))
    if c and climbed > 0:
        walked = [_along(k / 48.0 * f) for k in range(49)]
        out.append('<path class="walked" d="M %s" pathLength="1" stroke-dasharray="1 1" '
                   'stroke-dashoffset="0" fill="none" stroke="url(#cl-walk)" stroke-width="3.5" '
                   'stroke-linecap="round" stroke-linejoin="round" filter="url(#cl-glow)"/>'
                   % " L ".join("%.1f %.1f" % p for p in walked))
        for k, frac in enumerate((0.3, 0.62, 0.86)):
            if f * frac * (len(_ROUTE) - 1) < 0.6:
                continue                        # too close to the start to show
            sx, sy = _along(f * frac)
            out.append(_sparkle(sx + 6, sy - 12, 3.5, "spark s%d" % k))
    # the summit: a halo, a pole and a gold flag
    fx, fy = _along(1.0)
    out.append('<circle class="breathe" cx="%.1f" cy="%.1f" r="38" fill="url(#cl-halo)"/>' % (fx, fy - 14))
    out.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#fff" stroke-width="2" '
               'stroke-linecap="round"/>' % (fx, fy, fx, fy - 30))
    out.append('<path d="M %.1f %.1f Q %.1f %.1f %.1f %.1f Q %.1f %.1f %.1f %.1f Z" '
               'fill="var(--dream-gold)"/>'
               % (fx + 1, fy - 30, fx + 12, fy - 29, fx + 25, fy - 23, fx + 12, fy - 19, fx + 1, fy - 16))
    if not c:
        out.append("</svg>")
        return "".join(out)
    # the camps: passed ones lit gold, the next one ringed, the rest faint
    named = {0, n, reached, min(reached + 1, n)} if n > 5 else set(range(n + 1))
    for i, name in enumerate(labels):
        x, y = _along(i / float(n))
        passed = i <= reached
        nxt = i == min(reached + 1, n) and i != reached
        if passed:
            out.append('<circle cx="%.1f" cy="%.1f" r="5" fill="var(--dream-gold)" '
                       'filter="url(#cl-glow)"/>' % (x, y))
        elif nxt:
            out.append('<circle class="ring" cx="%.1f" cy="%.1f" r="6.5" fill="var(--dream-near)" '
                       'stroke="var(--dream-gold)" stroke-width="2.5"/>' % (x, y))
        else:
            out.append('<circle cx="%.1f" cy="%.1f" r="4" fill="var(--dream-near)" '
                       'stroke="#fff" stroke-width="1.5" opacity=".7"/>' % (x, y))
        if i not in named or i == reached:
            continue           # the climber stands on the camp reached
        if i == n:
            out.append('<text class="lbl dream" x="%.1f" y="%.1f" text-anchor="end" font-size="15" '
                       'font-weight="700" fill="var(--dream-gold)">%s</text>' % (x - 14, y + 5, name))
            continue
        if nxt:
            # beside the ring, away from the climber who stands just below it
            anchor, dx, dy = "start", 12, 22
        else:
            anchor, dx, dy = ("start" if i == 0 else "middle"), (6 if i == 0 else 0), \
                (28 if i % 2 == 0 else -16)
        out.append('<text class="lbl%s" x="%.1f" y="%.1f" text-anchor="%s" font-size="14" '
                   'font-weight="%s" fill="#fff" fill-opacity="%s">%s</text>'
                   % ("" if nxt else " mid", x + dx, y + dy, anchor,
                      "700" if nxt else "500", ".95" if nxt else ".7", name))
    # the climber: their own face, lit, with a tag
    out.append('<circle class="breathe" cx="%.1f" cy="%.1f" r="36" fill="url(#cl-halo)"/>' % (cx, cy))
    out.append('<circle class="pulse" cx="%.1f" cy="%.1f" r="18" fill="none" '
               'stroke="var(--dream-gold)" stroke-width="2"/>' % (cx, cy))
    face = ('<image href="%s" x="%.1f" y="%.1f" width="26" height="26" '
            'preserveAspectRatio="xMidYMid slice" clip-path="url(#cl-face)"/>'
            % (photo, cx - 13, cy - 13)) if photo else \
           ('<text x="%.1f" y="%.1f" font-size="17" text-anchor="middle" '
            'dominant-baseline="central">%s</text>' % (cx, cy + 1, avatar or "★"))
    out.append('<g class="me"><circle cx="%.1f" cy="%.1f" r="16" fill="var(--dream-deep)" '
               'stroke="var(--dream-gold)" stroke-width="3"/>%s</g>' % (cx, cy, face))
    tw, th = 52, 26
    tx = max(6.0, min(w - 6.0 - tw, cx - tw / 2.0))
    below = cy < 76
    ty = cy + 26 if below else cy - 26 - th
    tip = ('M %.1f %.1f L %.1f %.1f L %.1f %.1f Z' % (cx - 6, ty, cx + 6, ty, cx, ty - 7)) if below \
        else ('M %.1f %.1f L %.1f %.1f L %.1f %.1f Z' % (cx - 6, ty + th, cx + 6, ty + th, cx, ty + th + 7))
    out.append('<g class="tag"><rect x="%.1f" y="%.1f" width="%d" height="%d" rx="13" fill="#fff"/>'
               '<path d="%s" fill="#fff"/>'
               '<text x="%.1f" y="%.1f" text-anchor="middle" font-size="15" font-weight="700" '
               'fill="var(--dream-deep)">You</text></g>'
               % (tx, ty, tw, th, tip, tx + tw / 2.0, ty + 18))
    out.append("</svg>")
    return "".join(out)
