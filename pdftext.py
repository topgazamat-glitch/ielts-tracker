"""Pull the readable text out of a PDF, using pdfsplit's object parser.

There is no PDF tooling on this machine, so this does the small part of the
job that matters: work out what each font's byte codes mean, then walk the
content stream's text operators and put the characters back in reading order.

Two ways a font says what its bytes mean, and both appear in the same file:
a /ToUnicode CMap, or an /Encoding with a /Differences array of glyph names.
"""
import re
import sys

import pdfsplit

# glyph names that are not simply the character they draw
NAMED = {
    "space": " ", "period": ".", "comma": ",", "colon": ":", "semicolon": ";",
    "quotesingle": "'", "quotedbl": '"', "quoteright": "’",
    "quoteleft": "‘", "quotedblleft": "“", "quotedblright": "”",
    "hyphen": "-", "endash": "–", "emdash": "—", "bullet": "•",
    "parenleft": "(", "parenright": ")", "bracketleft": "[", "bracketright": "]",
    "braceleft": "{", "braceright": "}", "slash": "/", "backslash": "\\",
    "question": "?", "exclam": "!", "asterisk": "*", "ampersand": "&",
    "numbersign": "#", "percent": "%", "plus": "+", "equal": "=",
    "underscore": "_", "asciicircum": "^", "asciitilde": "~", "at": "@",
    "dollar": "$", "less": "<", "greater": ">", "bar": "|", "grave": "`",
    "copyright": "©", "registered": "®", "trademark": "™",
    "degree": "°", "section": "§", "paragraph": "¶",
    "ellipsis": "…", "guillemotleft": "«", "guillemotright": "»",
    "fi": "fi", "fl": "fl", "endash ": "–",
}
DIGITS = ["zero", "one", "two", "three", "four", "five", "six", "seven",
          "eight", "nine"]
for _i, _n in enumerate(DIGITS):
    NAMED[_n] = str(_i)


def glyph_char(name):
    name = str(name)
    if name in NAMED:
        return NAMED[name]
    if len(name) == 1:
        return name
    m = re.fullmatch(r"uni([0-9A-Fa-f]{4})", name)
    if m:
        return chr(int(m.group(1), 16))
    m = re.fullmatch(r"[A-Za-z]", name[:1]) and re.fullmatch(r"g?\d+", name[1:])
    return ""


def parse_tounicode(text):
    """bfchar and bfrange entries -> {code: string}."""
    out = {}
    for block in re.findall(r"beginbfchar(.*?)endbfchar", text, re.S):
        for src, dst in re.findall(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", block):
            out[int(src, 16)] = _utf16(dst)
    for block in re.findall(r"beginbfrange(.*?)endbfrange", text, re.S):
        for lo, hi, dst in re.findall(
                r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", block):
            start = int(dst, 16)
            for i, code in enumerate(range(int(lo, 16), int(hi, 16) + 1)):
                out[code] = chr(start + i)
        for lo, hi, arr in re.findall(
                r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*\[(.*?)\]", block, re.S):
            items = re.findall(r"<([0-9A-Fa-f]+)>", arr)
            for i, code in enumerate(range(int(lo, 16), int(hi, 16) + 1)):
                if i < len(items):
                    out[code] = _utf16(items[i])
    return out


def _utf16(hexstr):
    raw = bytes.fromhex(hexstr if len(hexstr) % 2 == 0 else "0" + hexstr)
    try:
        return raw.decode("utf-16-be")
    except UnicodeDecodeError:
        return ""


def font_map(doc, font):
    """code -> text, however this particular font chooses to say it."""
    font = doc.get(font) or {}
    tou = font.get("ToUnicode")
    if tou is not None:
        stream = doc.get(tou)
        if hasattr(stream, "data"):
            try:
                return parse_tounicode(stream.data().decode("latin-1")), True
            except Exception:
                pass
    enc = doc.get(font.get("Encoding"))
    table = {}
    if isinstance(enc, dict) and "Differences" in enc:
        code = 0
        for item in doc.get(enc["Differences"]) or []:
            if isinstance(item, (int, float)):
                code = int(item)
            else:
                table[code] = glyph_char(item)
                code += 1
    return table, False


class Text:
    """Accumulates glyphs and turns position changes into spaces and newlines."""

    def __init__(self):
        self.lines = []
        self.buf = []
        self.y = None

    def newline(self, dy=None):
        if self.buf:
            self.lines.append("".join(self.buf).rstrip())
            self.buf = []

    def add(self, s):
        self.buf.append(s)

    def gap(self, amount):
        # a big negative kern inside TJ is a word space
        if amount > 180 and self.buf and not self.buf[-1].endswith(" "):
            self.buf.append(" ")

    def done(self):
        self.newline()
        return [l for l in self.lines if l.strip()]


TOKEN = re.compile(rb"""
    (?P<str>\((?:\\.|[^\\()]|\((?:\\.|[^\\()])*\))*\))
  | (?P<hex><[0-9A-Fa-f\s]*>)
  | (?P<num>[-+]?\d*\.?\d+)
  | (?P<name>/[^\s/\[\]<>(){}]+)
  | (?P<op>[A-Za-z'"*]+)
  | (?P<open>\[) | (?P<close>\])
""", re.X)


def unescape(raw):
    out, i = bytearray(), 0
    body = raw[1:-1]
    while i < len(body):
        c = body[i]
        if c == 0x5C and i + 1 < len(body):
            nxt = body[i + 1]
            simple = {0x6E: 10, 0x72: 13, 0x74: 9, 0x62: 8, 0x66: 12}
            if nxt in simple:
                out.append(simple[nxt]); i += 2; continue
            if 0x30 <= nxt <= 0x37:
                digits = body[i + 1:i + 4]
                oct_ = re.match(rb"[0-7]{1,3}", digits).group(0)
                out.append(int(oct_, 8) & 0xFF); i += 1 + len(oct_); continue
            out.append(nxt); i += 2; continue
        out.append(c); i += 1
    return bytes(out)


def page_text(doc, page):
    contents = page.get("Contents")
    streams = contents if isinstance(contents, list) else [contents]
    raw = b""
    for st in streams:
        st = doc.get(st)
        if hasattr(st, "data"):
            try:
                raw += st.data() + b"\n"
            except Exception:
                pass
    res = doc.get(page.get("Resources")) or {}
    fonts = doc.get(res.get("Font")) or {}
    maps = {}

    def table_for(name):
        if name not in maps:
            maps[name] = font_map(doc, fonts.get(name)) if name in fonts else ({}, False)
        return maps[name]

    text, stack, cur = Text(), [], ("", ({}, False))
    for m in TOKEN.finditer(raw):
        kind = m.lastgroup
        val = m.group()
        if kind in ("str", "hex", "num", "name"):
            stack.append((kind, val))
            continue
        if kind in ("open", "close"):
            stack.append((kind, val))
            continue
        op = val.decode("latin-1")
        if op == "Tf":
            names = [v for k, v in stack if k == "name"]
            if names:
                nm = names[-1].decode("latin-1")[1:]
                cur = (nm, table_for(nm))
        elif op in ("Tj", "'", '"'):
            strs = [v for k, v in stack if k in ("str", "hex")]
            if strs:
                text.add(decode(strs[-1], cur[1]))
            if op in ("'", '"'):
                text.newline()
        elif op == "TJ":
            start = max((i for i, (k, _) in enumerate(stack) if k == "open"), default=None)
            if start is not None:
                for k, v in stack[start + 1:]:
                    if k in ("str", "hex"):
                        text.add(decode(v, cur[1]))
                    elif k == "num":
                        text.gap(-float(v))
        elif op in ("Td", "TD", "T*", "TL"):
            if op == "T*":
                text.newline()
            else:
                nums = [float(v) for k, v in stack if k == "num"]
                if len(nums) >= 2 and abs(nums[-1]) > 0.5:
                    text.newline()
        elif op in ("Tm", "BT", "ET"):
            text.newline()
        stack = []
    return text.done()


def decode(token, table_pair):
    table, is_cmap = table_pair
    if token.startswith(b"<"):
        hexs = re.sub(rb"\s", b"", token[1:-1]).decode("latin-1")
        if len(hexs) % 2:
            hexs += "0"
        codes = [int(hexs[i:i + 4] or "0", 16) for i in range(0, len(hexs), 4)] \
            if is_cmap and len(hexs) % 4 == 0 else \
            [int(hexs[i:i + 2], 16) for i in range(0, len(hexs), 2)]
    else:
        codes = list(unescape(token))
    out = []
    for c in codes:
        if c in table:
            out.append(table[c])
        elif not table and 32 <= c < 127:
            out.append(chr(c))
    return "".join(out)


def extract(path, first=None, last=None):
    doc = pdfsplit.Document(path)
    pages = doc.pages()
    lo = 0 if first is None else max(0, first - 1)
    hi = len(pages) if last is None else min(len(pages), last)
    for i in range(lo, hi):
        yield i + 1, page_text(doc, pages[i])


if __name__ == "__main__":
    path = sys.argv[1]
    a = int(sys.argv[2]) if len(sys.argv) > 2 else None
    b = int(sys.argv[3]) if len(sys.argv) > 3 else a
    for num, lines in extract(path, a, b):
        print("--- page %d ---" % num)
        for l in lines:
            print(l)
