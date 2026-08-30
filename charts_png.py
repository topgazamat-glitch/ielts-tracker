"""Progress charts rendered as PNG images, for sending into a Telegram chat."""
import core
import png

W, H = 760, 440
PAD_L, PAD_R, PAD_T, PAD_B = 58, 24, 74, 66
PW, PH = W - PAD_L - PAD_R, H - PAD_T - PAD_B

INK = (26, 26, 24)
MUTED = (122, 122, 116)
GRID = (228, 228, 222)
ACCENT = (47, 111, 78)
WARN = (180, 70, 60)
BAND = (176, 176, 168)


def _y(v):
    return PAD_T + PH * (1 - v / 10.0)


def _x(i, n):
    return PAD_L + (PW / 2 if n <= 1 else PW * i / (n - 1))


def _frame(c, title, subtitle):
    c.text(PAD_L - 2, 20, title[:34], INK, 2)
    if subtitle:
        c.text(PAD_L - 2, 46, subtitle[:60], MUTED, 1)
    for v in (0, 2, 4, 6, 8, 10):
        y = int(_y(v))
        c.hline(PAD_L, W - PAD_R, y, GRID)
        label = str(v)
        c.text(PAD_L - 12 - c.text_width(label), y - 3, label, MUTED, 1)
    c.hline(PAD_L, W - PAD_R, int(_y(0)), MUTED)


def _footer(c, left, y=None):
    c.text(PAD_L - 2, (c.h - 20) if y is None else y, left[:70], MUTED, 1)


def score_chart(title, subtitle, timeline, band=None, footer=""):
    """Rolling-3 trend line, raw score dots, misses marked on the baseline."""
    c = png.Canvas(W, H)
    _frame(c, title, subtitle)
    n = len(timeline)
    if n == 0:
        c.text(PAD_L, PAD_T + PH // 2, "no data yet", MUTED, 2)
        return c.to_png()

    scores = [t["score"] for t in timeline]
    roll = core.rolling_average(scores)

    if band:
        pts = [(i, v) for i, v in enumerate(band) if v is not None]
        for a, b in zip(pts, pts[1:]):
            c.line(_x(a[0], n), _y(a[1]), _x(b[0], n), _y(b[1]), BAND, 2)

    pts = [(i, v) for i, v in enumerate(roll) if v is not None]
    for a, b in zip(pts, pts[1:]):
        c.line(_x(a[0], n), _y(a[1]), _x(b[0], n), _y(b[1]), ACCENT, 3)

    baseline = int(_y(0)) + 16
    for i, t in enumerate(timeline):
        x = int(_x(i, n))
        if t["score"] is not None:
            c.disc(x, int(_y(t["score"])), 5, ACCENT)
        elif t.get("status") == "missing":
            c.cross(x, baseline, 5, WARN, 2)
        c.text(x - c.text_width(str(i + 1)) // 2, baseline + 12, str(i + 1), MUTED, 1)

    _footer(c, footer)
    return c.to_png()


def bars_chart(title, subtitle, rows, footer=""):
    """Horizontal 0-10 bars, one per label - group comparison at a glance.

    Height follows the number of rows so a small group gets a small image.
    """
    height = PAD_T + 28 * max(1, min(len(rows), 14)) + 46
    c = png.Canvas(W, height)
    c.text(PAD_L - 40, 20, title[:34], INK, 2)
    if subtitle:
        c.text(PAD_L - 40, 46, subtitle[:60], MUTED, 1)
    if not rows:
        c.text(PAD_L, PAD_T + 20, "no data yet", MUTED, 2)
        return c.to_png()

    rows = rows[:14]
    top, left = PAD_T, 190
    width = W - left - 90
    gap = 28
    for i, (label, value, flagged) in enumerate(rows):
        y = top + i * gap
        c.text(16, y + 4, label[:20], INK, 1)
        c.rect(left, y, width, 14, GRID)
        if value is not None:
            c.rect(left, y, max(2, int(width * value / 10.0)), 14, WARN if flagged else ACCENT)
            c.text(left + width + 10, y + 4, ("%g" % value) + "/10", MUTED, 1)
        else:
            c.text(left + width + 10, y + 4, "-", MUTED, 1)
    _footer(c, footer)
    return c.to_png()
