"""A minimal PDF writer: text, headings and page numbers, standard library only.

Enough to turn a pile of transcripts into a document a student can actually
read - real fonts, proper wrapping, a contents page and bookmarks.
"""
import zlib

PAGE_W, PAGE_H = 595.28, 841.89          # A4 in points
WIN_ANSI = {"‘": 0x91, "’": 0x92, "“": 0x93, "”": 0x94,
            "–": 0x96, "—": 0x97, "…": 0x85, "•": 0x95,
            " ": 0x20}

# Helvetica advance widths (1/1000 em) for the characters this document uses
_W = {32: 278, 33: 278, 34: 355, 35: 556, 36: 556, 37: 889, 38: 667, 39: 191,
      40: 333, 41: 333, 42: 389, 43: 584, 44: 278, 45: 333, 46: 278, 47: 278,
      58: 278, 59: 278, 60: 584, 61: 584, 62: 584, 63: 556, 64: 1015,
      91: 278, 92: 278, 93: 278, 94: 469, 95: 556, 96: 333,
      123: 334, 124: 260, 125: 334, 126: 584}
for _c in range(48, 58):
    _W[_c] = 556
for _c, _w in zip(range(65, 91),
                  [667, 667, 722, 722, 667, 611, 778, 722, 278, 500, 667, 556,
                   833, 722, 778, 667, 778, 722, 667, 611, 722, 667, 944, 667,
                   667, 611]):
    _W[_c] = _w
for _c, _w in zip(range(97, 123),
                  [556, 556, 500, 556, 556, 278, 556, 556, 222, 222, 500, 222,
                   833, 556, 556, 556, 556, 333, 500, 278, 556, 500, 722, 500,
                   500, 500]):
    _W[_c] = _w
_BOLD_EXTRA = {**_W}
for _c, _w in zip(range(65, 91),
                  [722, 722, 722, 722, 667, 611, 778, 722, 278, 556, 722, 611,
                   833, 722, 778, 667, 778, 722, 667, 611, 722, 667, 944, 667,
                   667, 611]):
    _BOLD_EXTRA[_c] = _w
for _c, _w in zip(range(97, 123),
                  [556, 611, 556, 611, 556, 333, 611, 611, 278, 278, 556, 278,
                   889, 611, 611, 611, 611, 389, 556, 333, 611, 556, 778, 556,
                   556, 500]):
    _BOLD_EXTRA[_c] = _w


def encode(text):
    out = bytearray()
    for ch in text:
        code = WIN_ANSI.get(ch)
        if code is None:
            code = ord(ch) if ord(ch) < 256 else 63     # '?' for anything exotic
        out.append(code)
    return bytes(out)


def width(text, size, bold=False):
    table = _BOLD_EXTRA if bold else _W
    total = sum(table.get(c, 556) for c in encode(text))
    return total * size / 1000.0


def wrap(text, size, max_width, bold=False):
    words, lines, line = text.split(), [], ""
    for word in words:
        trial = word if not line else line + " " + word
        if width(trial, size, bold) <= max_width or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def esc(text):
    return (encode(text).replace(b"\\", b"\\\\")
            .replace(b"(", b"\\(").replace(b")", b"\\)"))


class Doc:
    """Collects drawing operations page by page, then serialises them."""

    def __init__(self, margin=56):
        self.margin = margin
        self.pages = [[]]
        self.y = PAGE_H - margin
        self.outline = []          # (title, page index)

    # ---- layout helpers
    @property
    def page_no(self):
        return len(self.pages) - 1

    def new_page(self):
        self.pages.append([])
        self.y = PAGE_H - self.margin

    def space(self, amount):
        if self.y - amount < self.margin + 24:
            self.new_page()
        else:
            self.y -= amount

    def text(self, s, size=10.5, bold=False, indent=0, leading=None,
             colour=(0, 0, 0), gap_after=0):
        leading = leading or size * 1.42
        max_w = PAGE_W - 2 * self.margin - indent
        for line in wrap(s, size, max_w, bold):
            if self.y - leading < self.margin + 24:
                self.new_page()
            self.y -= leading
            self.pages[-1].append(
                ("text", self.margin + indent, self.y, line, size, bold, colour))
        if gap_after:
            self.space(gap_after)

    def rule(self, colour=(0.85, 0.85, 0.82), gap=6):
        self.space(gap)
        self.pages[-1].append(("rule", self.margin, self.y, PAGE_W - self.margin, colour))
        self.space(gap)

    def bookmark(self, title):
        self.outline.append((title, self.page_no))

    # ---- output
    def build(self, title="Document", footer=None):
        objects, page_ids = [], []
        font_regular, font_bold = 3, 4

        def add(body):
            objects.append(body)
            return len(objects) + 4          # object numbers start after the fixed ones

        streams = []
        for index, ops in enumerate(self.pages):
            parts = []
            for op in ops:
                if op[0] == "text":
                    _, x, y, line, size, bold, colour = op
                    parts.append(b"BT /F%d %.2f Tf %.3f %.3f %.3f rg %.2f %.2f Td (%s) Tj ET"
                                 % (2 if bold else 1, size, colour[0], colour[1],
                                    colour[2], x, y, esc(line)))
                elif op[0] == "rule":
                    _, x1, y, x2, colour = op
                    parts.append(b"%.3f %.3f %.3f RG 0.6 w %.2f %.2f m %.2f %.2f l S"
                                 % (colour[0], colour[1], colour[2], x1, y, x2, y))
            if footer:
                label = footer(index, len(self.pages))
                if label:
                    w = width(label, 8.5)
                    parts.append(b"BT /F1 8.5 Tf 0.55 0.55 0.53 rg %.2f %.2f Td (%s) Tj ET"
                                 % ((PAGE_W - w) / 2, 30, esc(label)))
            streams.append(zlib.compress(b"\n".join(parts)))

        out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = {}
        n_pages = len(streams)
        # 1 catalog, 2 pages, 3+4 fonts, then page objects and content streams
        first_page_obj = 5
        first_stream_obj = first_page_obj + n_pages
        outline_obj = first_stream_obj + n_pages
        n_outline = len(self.outline)

        def write(num, body):
            offsets[num] = len(out)
            out.extend(b"%d 0 obj\n" % num + body + b"\nendobj\n")

        kids = b" ".join(b"%d 0 R" % (first_page_obj + i) for i in range(n_pages))
        catalog = b"<< /Type /Catalog /Pages 2 0 R"
        if n_outline:
            catalog += b" /Outlines %d 0 R /PageMode /UseOutlines" % outline_obj
        catalog += b" >>"
        write(1, catalog)
        write(2, b"<< /Type /Pages /Count %d /Kids [%s] >>" % (n_pages, kids))
        write(3, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica"
                 b" /Encoding /WinAnsiEncoding >>")
        write(4, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold"
                 b" /Encoding /WinAnsiEncoding >>")
        for i in range(n_pages):
            write(first_page_obj + i,
                  b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %.2f %.2f]"
                  b" /Resources << /Font << /F1 3 0 R /F2 4 0 R >> >>"
                  b" /Contents %d 0 R >>" % (PAGE_W, PAGE_H, first_stream_obj + i))
        for i, stream in enumerate(streams):
            write(first_stream_obj + i,
                  b"<< /Length %d /Filter /FlateDecode >>\nstream\n" % len(stream)
                  + stream + b"\nendstream")
        if n_outline:
            first_item = outline_obj + 1
            write(outline_obj,
                  b"<< /Type /Outlines /First %d 0 R /Last %d 0 R /Count %d >>"
                  % (first_item, first_item + n_outline - 1, n_outline))
            for i, (label, page_index) in enumerate(self.outline):
                num = first_item + i
                body = (b"<< /Title (%s) /Parent %d 0 R /Dest [%d 0 R /Fit]"
                        % (esc(label), outline_obj, first_page_obj + page_index))
                if i:
                    body += b" /Prev %d 0 R" % (num - 1)
                if i < n_outline - 1:
                    body += b" /Next %d 0 R" % (num + 1)
                write(num, body + b" >>")

        highest = max(offsets)
        start = len(out)
        out.extend(b"xref\n0 %d\n0000000000 65535 f \n" % (highest + 1))
        for num in range(1, highest + 1):
            out.extend(b"%010d 00000 n \n" % offsets.get(num, 0))
        out.extend(b"trailer\n<< /Size %d /Root 1 0 R /Info << /Title (%s) >> >>\n"
                   b"startxref\n%d\n%%%%EOF\n" % (highest + 1, esc(title), start))
        return bytes(out)
