"""A tiny PNG writer and rasteriser - pure standard library.

This machine has no Pillow or matplotlib, and Telegram only displays real
images, so charts sent into a chat are drawn pixel by pixel here.
"""
import struct
import zlib

FONT_W, FONT_H = 5, 7
_GLYPHS = {
    " ": "00000/00000/00000/00000/00000/00000/00000",
    "0": "01110/10001/10011/10101/11001/10001/01110",
    "1": "00100/01100/00100/00100/00100/00100/01110",
    "2": "01110/10001/00001/00010/00100/01000/11111",
    "3": "11111/00010/00100/00010/00001/10001/01110",
    "4": "00010/00110/01010/10010/11111/00010/00010",
    "5": "11111/10000/11110/00001/00001/10001/01110",
    "6": "00110/01000/10000/11110/10001/10001/01110",
    "7": "11111/00001/00010/00100/01000/01000/01000",
    "8": "01110/10001/10001/01110/10001/10001/01110",
    "9": "01110/10001/10001/01111/00001/00010/01100",
    ".": "00000/00000/00000/00000/00000/01100/01100",
    ",": "00000/00000/00000/00000/01100/01100/11000",
    "/": "00001/00010/00010/00100/01000/01000/10000",
    "-": "00000/00000/00000/11111/00000/00000/00000",
    ":": "00000/01100/01100/00000/01100/01100/00000",
    "%": "11001/11010/00010/00100/01000/01011/10011",
    "+": "00000/00100/00100/11111/00100/00100/00000",
    "(": "00010/00100/01000/01000/01000/00100/00010",
    ")": "01000/00100/00010/00010/00010/00100/01000",
    "A": "01110/10001/10001/11111/10001/10001/10001",
    "B": "11110/10001/10001/11110/10001/10001/11110",
    "C": "01110/10001/10000/10000/10000/10001/01110",
    "D": "11100/10010/10001/10001/10001/10010/11100",
    "E": "11111/10000/10000/11110/10000/10000/11111",
    "F": "11111/10000/10000/11110/10000/10000/10000",
    "G": "01110/10001/10000/10111/10001/10001/01111",
    "H": "10001/10001/10001/11111/10001/10001/10001",
    "I": "01110/00100/00100/00100/00100/00100/01110",
    "J": "00111/00010/00010/00010/00010/10010/01100",
    "K": "10001/10010/10100/11000/10100/10010/10001",
    "L": "10000/10000/10000/10000/10000/10000/11111",
    "M": "10001/11011/10101/10101/10001/10001/10001",
    "N": "10001/11001/10101/10011/10001/10001/10001",
    "O": "01110/10001/10001/10001/10001/10001/01110",
    "P": "11110/10001/10001/11110/10000/10000/10000",
    "Q": "01110/10001/10001/10001/10101/10010/01101",
    "R": "11110/10001/10001/11110/10100/10010/10001",
    "S": "01111/10000/10000/01110/00001/00001/11110",
    "T": "11111/00100/00100/00100/00100/00100/00100",
    "U": "10001/10001/10001/10001/10001/10001/01110",
    "V": "10001/10001/10001/10001/10001/01010/00100",
    "W": "10001/10001/10001/10101/10101/11011/10001",
    "X": "10001/10001/01010/00100/01010/10001/10001",
    "Y": "10001/10001/01010/00100/00100/00100/00100",
    "Z": "11111/00001/00010/00100/01000/10000/11111",
}
FONT = {c: [r for r in g.split("/")] for c, g in _GLYPHS.items()}


class Canvas:
    def __init__(self, w, h, bg=(255, 255, 255)):
        self.w, self.h = w, h
        self.buf = bytearray(bytes(bg) * (w * h))

    def px(self, x, y, c):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i:i + 3] = bytes(c)

    def rect(self, x, y, w, h, c):
        for yy in range(int(y), int(y + h)):
            for xx in range(int(x), int(x + w)):
                self.px(xx, yy, c)

    def hline(self, x1, x2, y, c, t=1):
        for k in range(t):
            for x in range(int(min(x1, x2)), int(max(x1, x2)) + 1):
                self.px(x, y + k, c)

    def vline(self, x, y1, y2, c, t=1):
        for k in range(t):
            for y in range(int(min(y1, y2)), int(max(y1, y2)) + 1):
                self.px(x + k, y, c)

    def line(self, x1, y1, x2, y2, c, t=2):
        """Bresenham, thickened by stamping a small square at each step."""
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        dx, dy = abs(x2 - x1), -abs(y2 - y1)
        sx, sy = (1 if x1 < x2 else -1), (1 if y1 < y2 else -1)
        err = dx + dy
        off = t // 2
        while True:
            for a in range(t):
                for b in range(t):
                    self.px(x1 + a - off, y1 + b - off, c)
            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x1 += sx
            if e2 <= dx:
                err += dx
                y1 += sy

    def disc(self, cx, cy, r, c):
        for y in range(-r, r + 1):
            for x in range(-r, r + 1):
                if x * x + y * y <= r * r:
                    self.px(cx + x, cy + y, c)

    def cross(self, cx, cy, r, c, t=2):
        self.line(cx - r, cy - r, cx + r, cy + r, c, t)
        self.line(cx - r, cy + r, cx + r, cy - r, c, t)

    def text(self, x, y, s, c, scale=1):
        """Draws uppercase text; unknown characters become spaces."""
        cx = x
        for ch in s.upper():
            glyph = FONT.get(ch)
            if glyph is None:
                cx += (FONT_W + 1) * scale
                continue
            for ry, row in enumerate(glyph):
                for rxi, on in enumerate(row):
                    if on == "1":
                        self.rect(cx + rxi * scale, y + ry * scale, scale, scale, c)
            cx += (FONT_W + 1) * scale
        return cx

    def text_width(self, s, scale=1):
        return len(s) * (FONT_W + 1) * scale

    def to_png(self):
        raw = bytearray()
        stride = self.w * 3
        for y in range(self.h):
            raw.append(0)  # filter type 0
            raw += self.buf[y * stride:(y + 1) * stride]

        def chunk(tag, data):
            return (struct.pack(">I", len(data)) + tag + data
                    + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

        return (b"\x89PNG\r\n\x1a\n"
                + chunk(b"IHDR", struct.pack(">IIBBBBB", self.w, self.h, 8, 2, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(bytes(raw), 6))
                + chunk(b"IEND", b""))
