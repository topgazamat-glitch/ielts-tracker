"""The pictures in the parents' channel, drawn with real letters.

png.py draws charts in block capitals, which cannot write Азиза or oʻrtacha.
This draws with Roboto, letter by letter, from fonts/card.atlas (made once by
make_font.py): each letter is a small map of how dark its pixels are, laid
onto the picture in the colour asked for. Shapes are smoothed at the edges the
same way, so a bar or a badge does not look cut out with scissors.

Two pictures, both 1080 wide - the width a phone shows without shrinking:
  class_table  the class, one row a student: place, homework, mark, lesson,
               words, and the league points as a bar
  trend        the last weeks, a row each: how much homework was done, the
               average mark and the lesson marks, as bars with the figure
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
BG = (244, 243, 249)
SURFACE = (255, 255, 255)
INK = (28, 15, 34)
INK2 = (92, 60, 101)
INK3 = (133, 122, 140)
LINE = (230, 224, 235)
TRACK = (238, 232, 242)
BRAND = (112, 21, 137)
DEEP = (50, 10, 62)
LIFT = (144, 73, 163)
SOFT = (238, 227, 241)
OK = (3, 150, 80)
RED = (214, 45, 52)
WHITE = (255, 255, 255)
MEDALS = {1: (246, 190, 30), 2: (184, 184, 198), 3: (212, 141, 76)}

_ATLAS = None


def atlas():
    global _ATLAS
    if _ATLAS is None:
        _ATLAS = json.loads(zlib.decompress(open(ATLAS_PATH, "rb").read()).decode("utf-8"))
    return _ATLAS


def _glyph(font, ch):
    f = atlas()[font]
    g = f["glyphs"].get(ch)
    if g is None:
        g = f["glyphs"].get("?")
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
                d = math.hypot(xx + 0.5 - cx, yy + 0.5 - cy)
                cov = r + 0.5 - d
                if cov > 0:
                    self.blend(xx, yy, c, int(255 * min(1.0, cov)))

    # -- letters

    def measure(self, s, font):
        return sum(_glyph(font, ch)[0] for ch in s)

    def line_height(self, font):
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


def _n(x):
    if x is None:
        return "–"
    return ("%g" % round(x, 1)).replace(".", ",")


def _header(c, title, what, days, level, h):
    c.gradient(0, 0, W, h, DEEP, BRAND)
    c.write(48, 34, title, "b44", WHITE)
    c.write(48, 34 + 62, what, "m22", (236, 220, 242))
    c.write_right(W - 48, 38, days, "b30", WHITE)
    if level:
        c.write_right(W - 48, 38 + 46, level, "r18", (222, 200, 230))


def _footer(c, y, left):
    c.write(48, y, left, "r18", INK3)
    c.write_right(W - 48, y, "OlimovAzamat", "m18", INK2)


# ------------------------------------------------ the class, a row a student

COLS = [  # key, centre x, uzbek, russian
    ("homework", 500, "Vazifa", "Д/з"),
    ("average", 610, "Baho", "Оценка"),
    ("conduct", 714, "Dars", "Урок"),
    ("extra", 812, "", ""),
]
ROW_H = 62

# the fourth figure: words learnt where the class does vocabulary, else the
# handout parts checked, else the lessons - never a column of dashes
EXTRAS = [("words", "Soʻz", "Слова", "Yangi soʻzlar", "Новые слова"),
          ("parts", "Qism", "Части", "Qoʻllanma qismlari", "Части буклетов"),
          ("lessons", "Dars soni", "Уроков", "Darslar", "Уроков")]


def extra_of(rep):
    for key, *labels in EXTRAS:
        if any(r[key] for r in rep["rows"]):
            return (key, *labels)
    return EXTRAS[-1]


def class_table(rep, rows=None):
    """The class table as a PNG. `rows` narrows it to a slice of the class,
    for a class too long for one picture."""
    p = rep["period"]
    rows = rep["rows"] if rows is None else rows
    t, b = rep["totals"], rep["before"]
    head_h, tiles_y, tile_h = 176, 204, 136
    table_y = tiles_y + tile_h + 24
    body_y = table_y + 84
    h = body_y + max(1, len(rows)) * ROW_H + 24 + 70
    c = Card(W, h, BG)
    g = rep["group"]["name"]
    _header(c, "%s-guruh · Группа %s" % (g, g),
            "Oylik hisobot · Месячный отчёт" if p["monthly"] else "Haftalik hisobot · Недельный отчёт",
            "%s–%s" % (p["first"].strftime("%d.%m"), p["last"].strftime("%d.%m")),
            rep["level"], head_h)

    # four figures for the whole class, each against the stretch before
    def tile(i, value, change, uz, ru):
        tw = (W - 96 - 3 * 16) / 4
        x = 48 + i * (tw + 16)
        c.round_rect(x, tiles_y, tw, tile_h, 18, SURFACE)
        end = c.write(x + 22, tiles_y + 16, value, "b44", INK)
        if change:
            text, col = change
            c.write(end + 10, tiles_y + 36, text, "m18", col)
        c.write(x + 22, tiles_y + 80, uz, "m18", INK2)
        c.write(x + 22, tiles_y + 104, ru, "r18", INK3)

    def change(now, was, unit=""):
        if now is None or was is None:
            return None
        d = round(now - was, 1)
        if abs(d) < 0.05:
            return ("=", INK3)
        return (("▲ " if d > 0 else "▼ ") + _n(abs(d)) + unit, OK if d > 0 else RED)

    tile(0, "%d%%" % t["done_pct"] if t["done_pct"] is not None else "–",
         change(t["done_pct"], b["done_pct"]), "Vazifa bajarildi", "Д/з выполнено")
    tile(1, _n(t["average"]), change(t["average"], b["average"]), "Oʻrtacha baho", "Средняя оценка")
    tile(2, "%d%%" % t["conduct"] if t["conduct"] is not None else "–",
         change(t["conduct"], b["conduct"]), "Darsdagi faollik", "Работа на уроке")
    ex_key, ex_uz, ex_ru, ex_tile_uz, ex_tile_ru = extra_of(rep)
    total = (t["lessons"] if ex_key == "lessons"
             else sum(r[ex_key] for r in rep["rows"]))
    tile(3, str(total), None, ex_tile_uz, ex_tile_ru)

    # the table
    c.round_rect(48, table_y, W - 96, h - table_y - 70, 20, SURFACE)
    hy = table_y + 22
    c.write(76, hy, "Oʻrin · Ism", "m18", INK2)
    c.write(76, hy + 24, "Место · Имя", "r18", INK3)
    for key, cx, uz, ru in COLS:
        if key == "extra":
            uz, ru = ex_uz, ex_ru
        c.write_center(cx, hy, uz, "m18", INK2)
        c.write_center(cx, hy + 24, ru, "r18", INK3)
    pts_x, pts_w = 876, W - 48 - 28 - 876
    c.write(pts_x, hy, "Liga ballari" if rep["league"] else "Ball", "m18", INK2)
    c.write(pts_x, hy + 24, "Очки лиги" if rep["league"] else "Очки", "r18", INK3)
    c.fill(72, body_y - 10, W - 144, 2, LINE)

    top = max([r["season"] if rep["league"] else r["gained"] for r in rep["rows"]] + [0]) or 1
    for i, r in enumerate(rows):
        y = body_y + i * ROW_H
        if i:
            c.fill(72, y - 1, W - 144, 1, LINE)
        mid = y + ROW_H // 2 - 4
        rank = r["rank"]
        if rank:
            c.disc(96, mid, 19, MEDALS.get(rank, SOFT))
            c.write_center(96, mid - 14, str(rank), "b22",
                           WHITE if rank in MEDALS else INK2)
        else:
            c.write_center(96, mid - 14, "–", "b22", INK3)
        name = c.fit(r["student"]["name"], "m22", 300)
        c.write(132, mid - 15, name, "m22", INK)

        cells = {
            "homework": ("%d/%d" % (r["done"], r["set"]) if r["set"] else "–",
                         RED if r["missing"] else (OK if r["set"] else INK3)),
            "average": (_n(r["average"]), INK if r["average"] is not None else INK3),
            "conduct": ("%d%%" % r["conduct"] if r["conduct"] is not None else "–",
                        INK if r["conduct"] is not None else INK3),
            "extra": (str(r[ex_key]) if r[ex_key] else "–", INK if r[ex_key] else INK3),
        }
        for key, cx, _uz, _ru in COLS:
            text, col = cells[key]
            c.write_center(cx, mid - 15, text, "r22" if key != "homework" else "m22", col)

        value = r["season"] if rep["league"] else r["gained"]
        if value is not None:
            end = c.write(pts_x, mid - 22, _n(value), "b22", INK)
            if rep["league"] and r["gained"]:
                c.write(end + 8, mid - 18, "+" + _n(r["gained"]), "m18", OK)
            c.round_rect(pts_x, mid + 10, pts_w, 10, 5, TRACK)
            fill = int(pts_w * max(0.0, value) / top)
            if fill >= 10:
                c.round_rect(pts_x, mid + 10, fill, 10, 5, BRAND)
        else:
            c.write(pts_x, mid - 15, "–", "r22", INK3)

    _footer(c, h - 52, ("Oʻrin — liga boʻyicha, yashil + shu davrda olingan ball · "
                        "Место — по лиге, + очки за период") if rep["league"] else
            "Oʻrin — shu davrda olingan ball boʻyicha · Место — по очкам за период")
    return c.to_png()


# ------------------------------------------------ the last weeks

def trend(rep):
    weeks = rep["weeks"]
    sections = [("done_pct", "Vazifa bajarildi", "Д/з выполнено", 100, "%d%%", BRAND),
                ("average", "Oʻrtacha baho", "Средняя оценка", 10, None, LIFT),
                ("conduct", "Darsdagi faollik", "Работа на уроке", 100, "%d%%", OK)]
    sections = [s for s in sections if any(w[s[0]] is not None for w in weeks)]
    head_h = 150
    row_h, sec_head = 52, 76
    h = head_h + 28 + sum(sec_head + len(weeks) * row_h + 28 for _s in sections) + 60
    h = max(h, head_h + 200)
    c = Card(W, h, BG)
    g = rep["group"]["name"]
    c.gradient(0, 0, W, head_h, DEEP, BRAND)
    c.write(48, 30, "%s-guruh · Группа %s" % (g, g), "b44", WHITE)
    c.write(48, 92, "Haftalar boʻyicha · По неделям", "m22", (236, 220, 242))
    p = rep["period"]
    y = head_h + 28
    if not sections:
        c.write(48, y + 20, "Bu haftalarda hali baho yoʻq · Оценок пока нет", "r26", INK3)
    for key, uz, ru, most, fmt, col in sections:
        c.round_rect(48, y, W - 96, sec_head + len(weeks) * row_h + 8, 20, SURFACE)
        end = c.write(76, y + 22, uz, "b30", INK)
        c.write(end + 14, y + 30, ru, "r22", INK3)
        yy = y + sec_head
        for w in weeks:
            now = p["first"] <= w["first"] <= p["last"] or p["first"] <= w["last"] <= p["last"]
            label = "%s–%s" % (w["first"].strftime("%d.%m"), w["last"].strftime("%d.%m"))
            c.write(76, yy + 8, label, "m22" if now else "r22", INK if now else INK2)
            bx, bw = 250, W - 48 - 28 - 250 - 110
            c.round_rect(bx, yy + 12, bw, 22, 11, TRACK)
            v = w[key]
            if v is not None:
                fill = int(bw * max(0.0, min(1.0, v / float(most))))
                if fill >= 22:
                    c.round_rect(bx, yy + 12, fill, 22, 11, col)
                c.write_right(W - 76, yy + 4, fmt % v if fmt else _n(v), "b30", INK)
            else:
                c.write_right(W - 76, yy + 8, "–", "r22", INK3)
            yy += row_h
        y += sec_head + len(weeks) * row_h + 8 + 20
    _footer(c, h - 48, "Oy haftalari · Недели месяца" if p["monthly"] else
            "Qalin — shu hafta · Жирным — эта неделя")
    return c.to_png()
