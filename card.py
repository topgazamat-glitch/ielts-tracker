"""The pictures in the parents' channel, drawn with real letters, big enough
to read on a phone.

png.py draws charts in block capitals, which cannot write Азиза or oʻrtacha.
This draws with Roboto, letter by letter, from fonts/card.atlas (made once by
make_font.py): each letter is a small map of how dark its pixels are, laid
onto the picture in the colour asked for. Shapes are smoothed at the edges the
same way, so a bar or a dot does not look cut out with scissors.

The pictures are 1080 wide and a phone shows them about 390 wide, so nothing
is written smaller than 28 - about 10 on the phone.

  league   a class's league: each student's points, and what they gained
  student  one student's week: place, points, the marks from each lesson with
           the teacher's note, homework, points week by week, and a few
           sentences in Uzbek and Russian
"""
import base64
import json
import math
import os
import zlib

import png

ROOT = os.path.dirname(os.path.abspath(__file__))
ATLAS_PATH = os.path.join(ROOT, "fonts", "card.atlas")

W = 1080
M = 48                      # the picture's margin
PAD = 40                    # inside a white panel
BG = (244, 243, 249)
SURFACE = (255, 255, 255)
INK = (28, 15, 34)
INK2 = (92, 60, 101)
INK3 = (128, 117, 136)
LINE = (230, 224, 235)
TRACK = (236, 230, 241)
BRAND = (112, 21, 137)
DEEP = (50, 10, 62)
PALE = (214, 190, 224)
SOFT = (246, 240, 249)
OK = (3, 145, 78)
RED = (212, 43, 50)
WHITE = (255, 255, 255)
ON_BRAND = (236, 220, 242)
MEDALS = {1: (240, 180, 20), 2: (170, 170, 186), 3: (205, 132, 70)}
# the three lesson marks, each in its own colour, named above its column
CRITERIA = [("Vaqtida kelish", "Пунктуальность", (12, 128, 214)),
            ("Xulq", "Поведение", BRAND),
            ("Faollik", "Активность", OK)]

_ATLAS = None


def atlas():
    global _ATLAS
    if _ATLAS is None:
        _ATLAS = json.loads(zlib.decompress(open(ATLAS_PATH, "rb").read()).decode("utf-8"))
    return _ATLAS


def _glyph(font, ch):
    f = atlas()[font]
    g = f["glyphs"].get(ch) or f["glyphs"].get("?") or f["glyphs"][" "]
    if isinstance(g[5], str):
        g[5] = base64.b64decode(g[5]) if g[5] else b""
    return g


class Card(png.Canvas):

    def fill(self, x, y, w, h, c):
        x0, y0 = max(0, int(x)), max(0, int(y))
        x1, y1 = min(self.w, int(x + w)), min(self.h, int(y + h))
        if x1 <= x0:
            return
        row = bytes(c) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.buf[i:i + len(row)] = row

    def blend(self, x, y, c, a):
        """Lay colour c over pixel (x, y) at a/255 strength."""
        if a <= 0 or not (0 <= x < self.w and 0 <= y < self.h):
            return
        i = (y * self.w + x) * 3
        if a >= 255:
            self.buf[i:i + 3] = bytes(c)
            return
        b = self.buf
        k = 255 - a
        b[i] = (b[i] * k + c[0] * a) // 255
        b[i + 1] = (b[i + 1] * k + c[1] * a) // 255
        b[i + 2] = (b[i + 2] * k + c[2] * a) // 255

    def gradient(self, x, y, w, h, c1, c2):
        """Left to right, c1 into c2."""
        row = bytearray()
        for xx in range(int(w)):
            t = xx / max(1, w - 1)
            row += bytes(int(c1[k] + (c2[k] - c1[k]) * t) for k in range(3))
        for yy in range(int(y), int(y + h)):
            if 0 <= yy < self.h:
                i = (yy * self.w + int(x)) * 3
                self.buf[i:i + len(row)] = row

    def round_rect(self, x, y, w, h, r, c):
        x, y, w, h = int(x), int(y), int(w), int(h)
        r = max(0, min(r, h // 2, w // 2))
        for yy in range(h):
            if yy < r:
                dy = r - yy - 0.5
            elif yy >= h - r:
                dy = yy - (h - r) + 0.5
            else:
                self.fill(x, y + yy, w, 1, c)
                continue
            inset = r - math.sqrt(max(0.0, r * r - dy * dy))
            full = int(math.ceil(inset))
            self.fill(x + full, y + yy, w - 2 * full, 1, c)
            edge = full - 1
            a = int(255 * (full - inset))
            if edge >= 0 and a:
                self.blend(x + edge, y + yy, c, a)
                self.blend(x + w - 1 - edge, y + yy, c, a)

    def disc(self, cx, cy, r, c):
        for yy in range(int(cy - r - 1), int(cy + r + 2)):
            for xx in range(int(cx - r - 1), int(cx + r + 2)):
                cov = r + 0.5 - math.hypot(xx + 0.5 - cx, yy + 0.5 - cy)
                if cov > 0:
                    self.blend(xx, yy, c, int(255 * min(1.0, cov)))

    def ring(self, cx, cy, r, thick, share, c, track):
        """A doughnut: `share` of it (from the top, clockwise) in c."""
        inner = r - thick
        for yy in range(int(cy - r - 1), int(cy + r + 2)):
            for xx in range(int(cx - r - 1), int(cx + r + 2)):
                dx, dy = xx + 0.5 - cx, yy + 0.5 - cy
                d = math.hypot(dx, dy)
                cov = min(r + 0.5 - d, d - inner + 0.5, 1.0)
                if cov <= 0:
                    continue
                turn = (math.atan2(dx, -dy) / (2 * math.pi)) % 1.0
                self.blend(xx, yy, c if turn <= share else track, int(255 * cov))

    def crop(self, h):
        self.buf = self.buf[:h * self.w * 3]
        self.h = h

    # -- letters

    def measure(self, s, font):
        return sum(_glyph(font, ch)[0] for ch in s)

    def line_h(self, font):
        f = atlas()[font]
        return f["ascent"] + f["descent"]

    def write(self, x, y, s, font, c):
        """Text with its line box's top at y. Returns where it ended."""
        base = y + atlas()[font]["ascent"]
        pen = float(x)
        for ch in s:
            adv, ox, oy, w, h, alpha = _glyph(font, ch)
            if w:
                gx, gy = int(round(pen)) + ox, base + oy
                j = 0
                for yy in range(gy, gy + h):
                    for xx in range(gx, gx + w):
                        a = alpha[j]
                        j += 1
                        if a:
                            self.blend(xx, yy, c, a)
            pen += adv
        return pen

    def write_right(self, xr, y, s, font, c):
        return self.write(xr - self.measure(s, font), y, s, font, c)

    def write_center(self, cx, y, s, font, c):
        return self.write(cx - self.measure(s, font) / 2, y, s, font, c)

    def fit(self, s, font, width):
        """s, shortened with an ellipsis until it fits."""
        if self.measure(s, font) <= width:
            return s
        while s and self.measure(s + "…", font) > width:
            s = s[:-1]
        return s.rstrip() + "…"

    def wrap(self, text, font, width):
        """The lines `text` breaks into at `width`."""
        lines = []
        for para in (text or "").split("\n"):
            line = ""
            for word in para.split():
                trial = (line + " " + word).strip()
                if self.measure(trial, font) <= width or not line:
                    line = trial
                else:
                    lines.append(line)
                    line = word
            lines.append(line)
        return lines


def _n(x):
    if x is None:
        return "–"
    return ("%g" % round(x, 1)).replace(".", ",")


def _days(p):
    return "%s–%s" % (p["first"].strftime("%d.%m"), p["last"].strftime("%d.%m"))


def _panel_title(c, y, uz, ru):
    """A panel's heading, Uzbek then Russian on one line. Returns the y below."""
    end = c.write(M + PAD, y, uz, "b40", INK)
    c.write(end + 16, y + 8, ru, "r32", INK3)
    return y + 64


# ------------------------------------------------ the class's league

LEAGUE_ROW = 112


def league(rep, rows=None, first=0):
    """A class's league as a PNG: each student's points and the week's gain.
    `rows`/`first` draw a slice of a long class, numbered on from `first`."""
    p = rep["period"]
    rows = rep["rows"] if rows is None else rows
    g = rep["group"]["name"]
    head_h = 236
    table_y = head_h + 28
    body_y = table_y + PAD + 76
    h = body_y + max(1, len(rows)) * LEAGUE_ROW + 24 + 96
    c = Card(W, h, BG)
    c.gradient(0, 0, W, head_h, DEEP, BRAND)
    c.write(M + 8, 44, "%s-guruh · Liga" % g, "b56", WHITE)
    c.write(M + 8, 124, "Группа %s · Лига" % g, "m32", ON_BRAND)
    c.write_right(W - M - 8, 52, _days(p), "b40", WHITE)
    c.write_right(W - M - 8, 112, "Oylik · Месяц" if p["monthly"] else "Hafta · Неделя",
                  "r28", ON_BRAND)

    c.round_rect(M, table_y, W - 2 * M, h - table_y - 96, 32, SURFACE)
    league_on = rep["league"]
    total_x, gain_x = 800, W - M - PAD            # the two figures' right edges
    hy = table_y + PAD - 6
    c.write(M + PAD, hy, "Oʻrin · Ism", "m28", INK2)
    c.write(M + PAD, hy + 34, "Место · Имя", "r28", INK3)
    if league_on:
        c.write_right(total_x, hy, "Jami", "m28", INK2)
        c.write_right(total_x, hy + 34, "Всего", "r28", INK3)
    c.write_right(gain_x, hy, "Shu hafta" if not p["monthly"] else "Shu oy", "m28", OK)
    c.write_right(gain_x, hy + 34, "За неделю" if not p["monthly"] else "За месяц", "r28", INK3)
    c.fill(M + PAD - 8, body_y - 12, W - 2 * M - 2 * PAD + 16, 2, LINE)

    top = max([(r["season"] if league_on else r["gained"]) or 0 for r in rep["rows"]] + [0]) or 1
    bar_x, bar_w = M + PAD + 84, (total_x - 150) - (M + PAD + 84) if league_on else 620
    for i, r in enumerate(rows):
        y = body_y + i * LEAGUE_ROW
        if i:
            c.fill(M + PAD - 8, y - 1, W - 2 * M - 2 * PAD + 16, 1, LINE)
        mid = y + LEAGUE_ROW // 2 - 6
        rank = r["rank"]
        cx = M + PAD + 30
        if rank:
            c.disc(cx, mid, 30, MEDALS.get(rank, TRACK))
            c.write_center(cx, mid - 20, str(rank), "b32", WHITE if rank in MEDALS else INK2)
        else:
            c.write_center(cx, mid - 20, "–", "b32", INK3)
        name = c.fit(r["student"]["name"], "m32", bar_w)
        c.write(bar_x, mid - 36, name, "m32", INK)
        value = (r["season"] if league_on else r["gained"]) or 0
        c.round_rect(bar_x, mid + 16, bar_w, 16, 8, TRACK)
        fill = int(bar_w * max(0.0, value) / top)
        if fill >= 16:
            c.round_rect(bar_x, mid + 16, fill, 16, 8, BRAND)
        if league_on:
            c.write_right(total_x, mid - 26, _n(r["season"]) if r["season"] is not None else "–",
                          "b40", INK)
        gained = r["gained"]
        c.write_right(gain_x, mid - 26, ("+" + _n(gained)) if gained else "0", "b40",
                      OK if gained else INK3)

    c.write(M + 8, h - 70, "Ball: uy vazifasi va darsdagi baholar · Очки: домашка и оценки на уроке",
            "r28", INK3)
    return c.to_png()


# ------------------------------------------------ one student

def student(r, rep):
    """One student's week (or month) as a PNG."""
    import parents
    p = rep["period"]
    g = rep["group"]["name"]
    c = Card(W, 6000, BG)
    inner_l, inner_r = M + PAD, W - M - PAD

    # the heading
    head_h = 250
    c.gradient(0, 0, W, head_h, DEEP, BRAND)
    c.write(M + 8, 40, c.fit(r["student"]["name"], "b56", W - 2 * M - 250), "b56", WHITE)
    c.write(M + 8, 122, "%s-guruh · Группа %s%s" % (g, g, (" · " + rep["level"]) if rep["level"] else ""),
            "m28", ON_BRAND)
    c.write(M + 8, 170, "Oylik hisobot · Месячный отчёт" if p["monthly"]
            else "Haftalik hisobot · Недельный отчёт", "r28", ON_BRAND)
    c.write_right(W - M - 8, 48, _days(p), "b40", WHITE)

    # three figures: place, points, homework
    y = head_h + 32
    tile_w, tile_h = (W - 2 * M - 2 * 20) / 3.0, 300
    labels = [("Guruhda oʻrin", "Место в группе"),
              ("Shu oy ball" if p["monthly"] else "Shu hafta ball",
               "Очки за месяц" if p["monthly"] else "Очки за неделю"),
              ("Uy vazifasi", "Домашка")]
    for i, (uz, ru) in enumerate(labels):
        x = M + i * (tile_w + 20)
        c.round_rect(x, y, tile_w, tile_h, 32, SURFACE)
        c.write_center(x + tile_w / 2, y + tile_h - 92, uz, "m28", INK2)
        c.write_center(x + tile_w / 2, y + tile_h - 56, ru, "r28", INK3)
        cx = x + tile_w / 2
        if i == 0:
            if r["rank"]:
                big, small = str(r["rank"]), "/%d" % rep["size"]
                wb, ws = c.measure(big, "b88"), c.measure(small, "m32")
                left = cx - (wb + ws) / 2
                end = c.write(left, y + 36, big, "b88", INK)
                c.write(end + 4, y + 88, small, "m32", INK3)
            else:
                c.write_center(cx, y + 36, "–", "b88", INK3)
        elif i == 1:
            gained = r["gained"]
            text = ("+" + _n(gained)) if gained else "0"
            font = "b88" if c.measure(text, "b88") <= tile_w - 40 else "b56"
            c.write_center(cx, y + (36 if font == "b88" else 58), text, font, OK if gained else INK3)
            if rep["league"] and r["season"] is not None:
                c.write_center(cx, y + 146, "Jami · Всего %s" % _n(r["season"]), "r28", INK3)
        else:
            share = (r["done"] / float(r["set"])) if r["set"] else 0.0
            c.ring(cx, y + 100, 72, 20, share, BRAND if r["missing"] == 0 else RED, TRACK)
            text = "%d/%d" % (r["done"], r["set"]) if r["set"] else "–"
            c.write_center(cx, y + 76, text, "b40", INK if r["set"] else INK3)
    y += tile_h + 28

    # the lessons: three marks as five dots each, and the teacher's note
    ls = r["lessons"]
    top = _panel_open(c, y)
    y = _panel_title(c, y + PAD, "Darsdagi baholar", "Оценки на уроке")
    cols = [440, 670, 900]
    if ls:
        c.write(inner_l, y, "Kun", "m28", INK2)
        c.write(inner_l, y + 34, "День", "r28", INK3)
        for (uz, ru, col), cx in zip(CRITERIA, cols):
            c.write_center(cx, y, uz, "m28", col)
            c.write_center(cx, y + 34, ru, "r28", INK3)
        y += 84
        for i, l in enumerate(ls):
            c.fill(inner_l, y, inner_r - inner_l, 1, LINE)
            y += 18
            wd = l["day"].weekday()
            c.write(inner_l, y, l["day"].strftime("%d.%m"), "m32", INK)
            c.write(inner_l, y + 40, "%s · %s" % (parents.UZ_DAY[wd], parents.RU_DAY[wd]), "r28", INK3)
            for (uz, ru, col), cx, v in zip(CRITERIA, cols, l["marks"]):
                if v is None:
                    c.write_center(cx, y + 14, "–", "m32", INK3)
                    continue
                for k in range(5):
                    c.disc(cx - 72 + k * 36, y + 36, 13, col if k < v else TRACK)
            y += 84
            if l["note"]:
                lines = c.wrap(l["note"], "r28", inner_r - inner_l - 48)
                box_h = 24 + 36 + len(lines) * 40 + 16
                c.round_rect(inner_l, y, inner_r - inner_l, box_h, 20, SOFT)
                c.write(inner_l + 24, y + 18, "Oʻqituvchi izohi · Заметка учителя", "m28", INK2)
                for j, line in enumerate(lines):
                    c.write(inner_l + 24, y + 60 + j * 40, line, "r28", INK)
                y += box_h + 16
        c.fill(inner_l, y, inner_r - inner_l, 1, LINE)
        y += 20
        c.write(inner_l, y, "Oʻrtacha · Среднее", "m28", INK2)
        c.write_right(inner_r, y - 4, "%s / 5" % _n(r["conduct"]), "b40", INK)
        y += 60
    else:
        c.write(inner_l, y, "Darsda baho qoʻyilmagan", "r32", INK3)
        c.write(inner_l, y + 42, "Оценок за урок нет", "r28", INK3)
        y += 92
    _panel_close(c, top, y + PAD - 20)
    y += PAD - 20 + 28

    # homework, a row a piece
    top = _panel_open(c, y)
    y = _panel_title(c, y + PAD, "Uy vazifalari", "Домашние задания")
    items = r["items"]
    if items:
        for i, it in enumerate(items):
            if i:
                c.fill(inner_l, y, inner_r - inner_l, 1, LINE)
            y += 16
            c.write(inner_l, y, c.fit(it["title"], "m32", 560), "m32", INK)
            due = core_day(it["due"])
            if due:
                c.write(inner_l, y + 42, "Muddat · Срок %s" % due, "r28", INK3)
            _homework_state(c, inner_r, y, it)
            y += 92
    else:
        c.write(inner_l, y, "Uy vazifasi yoʻq", "r32", INK3)
        c.write(inner_l, y + 42, "Заданий не было", "r28", INK3)
        y += 92
    _panel_close(c, top, y + PAD - 20)
    y += PAD - 20 + 28

    # points, week by week
    top = _panel_open(c, y)
    y = _panel_title(c, y + PAD, "Haftalar boʻyicha ball", "Очки по неделям")
    weekly = r["weekly"]
    chart_h = 220
    slot = (inner_r - inner_l) / float(max(1, len(weekly)))
    most = max([v for _w, v in weekly] + [1])
    base = y + 52 + chart_h
    for i, (w, v) in enumerate(weekly):
        now = w["first"] <= p["last"] and w["last"] >= p["first"]
        cx = inner_l + slot * (i + 0.5)
        col_h = max(8, int(chart_h * (v or 0) / most))
        c.round_rect(cx - 40, base - col_h, 80, col_h, 14, BRAND if now else PALE)
        c.write_center(cx, base - col_h - 46, _n(v) if v else "0", "b32", INK if now else INK2)
        c.write_center(cx, base + 14, w["first"].strftime("%d.%m"), "m28" if now else "r28",
                       INK if now else INK3)
    c.fill(inner_l, base, inner_r - inner_l, 2, LINE)
    y = base + 62
    _panel_close(c, top, y + PAD - 20)
    y += PAD - 20 + 28

    # in words
    top = _panel_open(c, y)
    y = _panel_title(c, y + PAD, "Xulosa", "Итог")
    for text, col in ((parents.summary_uz(r, rep), INK), (parents.summary_ru(r, rep), INK2)):
        for line in c.wrap(text, "r32", inner_r - inner_l):
            c.write(inner_l, y, line, "r32", col)
            y += 46
        y += 20
    _panel_close(c, top, y + PAD - 40)
    y += PAD - 40 + 28

    c.write(M + 8, y + 8, "%s · %s" % (parents.span_uz(p["first"], p["last"]),
                                       parents.span_ru(p["first"], p["last"])), "r28", INK3)
    c.write_right(W - M - 8, y + 8, "OlimovAzamat", "m28", INK2)
    c.crop(y + 72)
    return c.to_png()


def _panel_open(c, top):
    """A white panel from `top` down, its height not yet known: everything
    below turns white, and _panel_close gives back what is past its end."""
    c.fill(M, top, W - 2 * M, c.h - top, SURFACE)
    return top


def _panel_close(c, top, bottom, r=32):
    c.fill(M, bottom, W - 2 * M, c.h - bottom, BG)
    for cy, rows in ((top + r, range(top, top + r)), (bottom - r, range(bottom - r, bottom))):
        for cx in (M + r, W - M - r):
            for yy in rows:
                for xx in (range(M, M + r) if cx < W / 2 else range(W - M - r, W - M)):
                    cov = r + 0.5 - math.hypot(xx + 0.5 - cx, yy + 0.5 - cy)
                    if cov < 1:
                        c.blend(xx, yy, BG, int(255 * min(1.0, 1 - max(0.0, cov))))


def core_day(stamp):
    """'24.09' in the teacher's timezone, from a stored stamp."""
    if not stamp:
        return ""
    import core
    from datetime import timedelta
    return (core.parse(stamp) + timedelta(hours=core.load_config()["timezone_offset_hours"])
            ).strftime("%d.%m")


def _homework_state(c, xr, y, it):
    state = it["state"]
    if state in ("marked", "late"):
        mark = it["mark"]
        col = OK if mark is not None and mark >= 8 else (RED if mark is not None and mark < 5 else INK)
        end_w = c.measure("/10", "m28")
        c.write_right(xr - end_w - 4, y - 6, _n(mark), "b40", col)
        c.write_right(xr, y + 6, "/10", "m28", INK3)
        if state == "late":
            c.write_right(xr, y + 44, "Kechikib · С опозданием", "r28", RED)
        return
    uz, ru, col = {"missing": ("Topshirilmagan", "Не сдано", RED),
                   "waiting": ("Tekshirilmoqda", "Проверяется", INK2),
                   "pending": ("Muddati kelmagan", "Ещё не срок", INK2)}[state]
    c.write_right(xr, y, uz, "m28", col)
    c.write_right(xr, y + 36, ru, "r28", INK3 if state != "missing" else col)
