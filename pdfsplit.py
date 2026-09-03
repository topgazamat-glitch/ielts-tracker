"""Read a PDF, pull out chosen pages, write them to a new PDF.

Handles the modern parts of the format this needs - cross-reference streams and
object streams - because there is no PDF tooling on this machine. Pages are
copied object for object, so the result is lossless: same fonts, same images,
same quality as the book it came from.
"""
import re
import zlib

WHITESPACE = b"\x00\t\n\x0c\r "
DELIM = b"()<>[]{}/%"


class Ref:
    __slots__ = ("num", "gen")

    def __init__(self, num, gen=0):
        self.num, self.gen = num, gen

    def __repr__(self):
        return "%d %d R" % (self.num, self.gen)

    def __eq__(self, other):
        return isinstance(other, Ref) and (self.num, self.gen) == (other.num, other.gen)

    def __hash__(self):
        return hash((self.num, self.gen))


class Name(str):
    """A PDF /Name, kept distinct from a string so it serialises correctly."""


class Stream:
    def __init__(self, dictionary, raw):
        self.dict, self.raw = dictionary, raw

    def data(self):
        """Decoded bytes, for the filters this file actually uses."""
        filters = self.dict.get("Filter")
        if filters is None:
            return self.raw
        if isinstance(filters, Name):
            filters = [filters]
        out = self.raw
        for f in filters:
            if f == "FlateDecode":
                out = zlib.decompress(out)
                params = self.dict.get("DecodeParms") or {}
                if isinstance(params, list):
                    params = params[0] if params else {}
                if params and params.get("Predictor", 1) > 1:
                    out = undo_predictor(out, params)
            else:
                raise ValueError("unsupported filter: %s" % f)
        return out


def undo_predictor(data, params):
    """PNG predictors, as used by cross-reference streams."""
    colors = params.get("Colors", 1)
    bpc = params.get("BitsPerComponent", 8)
    columns = params.get("Columns", 1)
    bpp = max(1, (colors * bpc + 7) // 8)
    row_len = (columns * colors * bpc + 7) // 8
    out = bytearray()
    prev = bytearray(row_len)
    i = 0
    while i < len(data):
        ft = data[i]
        row = bytearray(data[i + 1:i + 1 + row_len])
        i += 1 + row_len
        if ft == 1:
            for j in range(bpp, len(row)):
                row[j] = (row[j] + row[j - bpp]) & 0xFF
        elif ft == 2:
            for j in range(len(row)):
                row[j] = (row[j] + prev[j]) & 0xFF
        elif ft == 3:
            for j in range(len(row)):
                left = row[j - bpp] if j >= bpp else 0
                row[j] = (row[j] + ((left + prev[j]) >> 1)) & 0xFF
        elif ft == 4:
            for j in range(len(row)):
                a = row[j - bpp] if j >= bpp else 0
                b = prev[j]
                c = prev[j - bpp] if j >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pred = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                row[j] = (row[j] + pred) & 0xFF
        out += row
        prev = row
    return bytes(out)


class Lexer:
    def __init__(self, data, pos=0):
        self.data, self.pos = data, pos

    def skip(self):
        d, n = self.data, len(self.data)
        while self.pos < n:
            c = d[self.pos]
            if c in WHITESPACE:
                self.pos += 1
            elif c == 0x25:                      # % comment
                while self.pos < n and d[self.pos] not in b"\r\n":
                    self.pos += 1
            else:
                return

    def token(self):
        self.skip()
        d = self.data
        if self.pos >= len(d):
            return None
        c = d[self.pos]
        if c == 0x2F:                            # /Name
            self.pos += 1
            start = self.pos
            while self.pos < len(d) and d[self.pos] not in WHITESPACE and d[self.pos] not in DELIM:
                self.pos += 1
            raw = d[start:self.pos]
            return Name(re.sub(rb"#([0-9A-Fa-f]{2})",
                               lambda m: bytes([int(m.group(1), 16)]), raw).decode("latin-1"))
        if d.startswith(b"<<", self.pos):
            self.pos += 2
            return "<<"
        if d.startswith(b">>", self.pos):
            self.pos += 2
            return ">>"
        if c == 0x5B:
            self.pos += 1
            return "["
        if c == 0x5D:
            self.pos += 1
            return "]"
        if c == 0x28:                            # (literal string)
            self.pos += 1
            depth, out = 1, bytearray()
            escapes = {0x6E: 10, 0x72: 13, 0x74: 9, 0x62: 8, 0x66: 12,
                       0x28: 0x28, 0x29: 0x29, 0x5C: 0x5C}
            while self.pos < len(d):
                ch = d[self.pos]
                if ch == 0x5C:
                    self.pos += 1
                    nxt = d[self.pos]
                    if nxt in escapes:
                        out.append(escapes[nxt]); self.pos += 1
                    elif 0x30 <= nxt <= 0x37:    # octal
                        digits = ""
                        while len(digits) < 3 and 0x30 <= d[self.pos] <= 0x37:
                            digits += chr(d[self.pos]); self.pos += 1
                        out.append(int(digits, 8) & 0xFF)
                    elif nxt in (10, 13):        # line continuation
                        self.pos += 1
                        if nxt == 13 and d[self.pos:self.pos + 1] == b"\n":
                            self.pos += 1
                    else:
                        out.append(nxt); self.pos += 1
                    continue
                if ch == 0x28:
                    depth += 1
                elif ch == 0x29:
                    depth -= 1
                    if depth == 0:
                        self.pos += 1
                        break
                out.append(ch)
                self.pos += 1
            return bytes(out)
        if c == 0x3C:                            # <hex string>
            end = d.index(b">", self.pos)
            raw = d[self.pos + 1:end]
            self.pos = end + 1
            return bytes.fromhex(re.sub(rb"[^0-9A-Fa-f]", b"", raw).decode() or "")
        start = self.pos
        while self.pos < len(d) and d[self.pos] not in WHITESPACE and d[self.pos] not in DELIM:
            self.pos += 1
        word = d[start:self.pos]
        if not word:
            self.pos += 1
            return self.token()
        return word.decode("latin-1")


class Parser:
    """Turns tokens into Python values, resolving object references lazily."""

    def __init__(self, data, pos=0, doc=None):
        self.lex = Lexer(data, pos)
        self.doc = doc

    def parse(self, token=None):
        t = self.lex.token() if token is None else token
        if t is None:
            return None
        if t == "<<":
            out = {}
            while True:
                key = self.lex.token()
                if key == ">>" or key is None:
                    break
                out[str(key)] = self.parse()
            # a dictionary may be followed by a stream
            save = self.lex.pos
            nxt = self.lex.token()
            if nxt == "stream":
                d = self.lex.data
                p = self.lex.pos
                if d.startswith(b"\r\n", p):
                    p += 2
                elif d[p:p + 1] in (b"\n", b"\r"):
                    p += 1
                length = out.get("Length")
                if isinstance(length, Ref) and self.doc:
                    length = self.doc.get(length)
                if not isinstance(length, int):
                    end = d.index(b"endstream", p)
                    length = end - p
                raw = d[p:p + length]
                self.lex.pos = p + length
                tail = self.lex.token()
                if tail != "endstream":                # length was wrong: recover
                    end = d.index(b"endstream", p)
                    raw = d[p:end].rstrip(b"\r\n")
                    self.lex.pos = end + len(b"endstream")
                return Stream(out, raw)
            self.lex.pos = save
            return out
        if t == "[":
            out = []
            while True:
                save = self.lex.pos
                nxt = self.lex.token()
                if nxt == "]" or nxt is None:
                    break
                self.lex.pos = save
                out.append(self.parse())
            return out
        if isinstance(t, (Name, bytes)):
            return t
        if t == "true":
            return True
        if t == "false":
            return False
        if t == "null":
            return None
        if re.fullmatch(r"[+-]?\d+", t):
            # could be "12 0 R" or "12 0 obj"
            save = self.lex.pos
            second = self.lex.token()
            if second is not None and re.fullmatch(r"\d+", str(second)):
                third = self.lex.token()
                if third == "R":
                    return Ref(int(t), int(second))
            self.lex.pos = save
            return int(t)
        if re.fullmatch(r"[+-]?(\d*\.\d*|\d+)", t):
            return float(t)
        return t


class Document:
    def __init__(self, path):
        self.data = open(path, "rb").read()
        self.offsets = {}          # obj num -> byte offset
        self.compressed = {}       # obj num -> (container stream num, index)
        self.cache = {}
        self.trailer = {}
        self._read_xref()

    # ---- cross-reference tables
    def _read_xref(self):
        m = re.search(rb"startxref\s+(\d+)\s*%%EOF\s*$", self.data[-2048:])
        if not m:
            raise ValueError("no startxref")
        seen, start = set(), int(m.group(1))
        while start is not None and start not in seen:
            seen.add(start)
            start = self._read_xref_section(start)

    def _read_xref_section(self, offset):
        lex = Lexer(self.data, offset)
        save = lex.pos
        token = lex.token()
        if token == "xref":
            return self._read_xref_table(lex)
        lex.pos = save
        parser = Parser(self.data, save, self)
        parser.lex.token(); parser.lex.token(); parser.lex.token()   # num gen obj
        stream = parser.parse()
        return self._read_xref_stream(stream)

    def _read_xref_table(self, lex):
        while True:
            save = lex.pos
            first = lex.token()
            if first == "trailer":
                trailer = Parser(self.data, lex.pos, self).parse()
                for k, v in trailer.items():
                    self.trailer.setdefault(k, v)
                if "XRefStm" in trailer:
                    self._read_xref_section(int(trailer["XRefStm"]))
                prev = trailer.get("Prev")
                return int(prev) if prev is not None else None
            if first is None:
                return None
            count = int(lex.token())
            start = int(first)
            lex.skip()
            for i in range(count):
                entry = self.data[lex.pos:lex.pos + 20]
                lex.pos += 20
                if entry[17:18] == b"n":
                    self.offsets.setdefault(start + i, int(entry[0:10]))

    def _read_xref_stream(self, stream):
        d = stream.dict
        for k, v in d.items():
            self.trailer.setdefault(k, v)
        widths = [int(x) for x in d["W"]]
        size = int(d["Size"])
        index = d.get("Index") or [0, size]
        index = [int(x) for x in index]
        raw = stream.data()
        row = sum(widths)
        pos = 0
        for i in range(0, len(index), 2):
            start, count = index[i], index[i + 1]
            for n in range(count):
                if pos + row > len(raw):
                    break
                fields, at = [], pos
                for w in widths:
                    fields.append(int.from_bytes(raw[at:at + w], "big") if w else None)
                    at += w
                pos += row
                num = start + n
                kind = fields[0] if widths[0] else 1
                if kind == 1 and num not in self.offsets and num not in self.compressed:
                    self.offsets[num] = fields[1]
                elif kind == 2 and num not in self.offsets and num not in self.compressed:
                    self.compressed[num] = (fields[1], fields[2])
        prev = d.get("Prev")
        return int(prev) if prev is not None else None

    # ---- objects
    def get(self, ref):
        if not isinstance(ref, Ref):
            return ref
        if ref.num in self.cache:
            return self.cache[ref.num]
        value = None
        if ref.num in self.offsets:
            parser = Parser(self.data, self.offsets[ref.num], self)
            parser.lex.token(); parser.lex.token()
            if parser.lex.token() == "obj":
                value = parser.parse()
        elif ref.num in self.compressed:
            container, _index = self.compressed[ref.num]
            for num, val in self._object_stream(container).items():
                self.cache.setdefault(num, val)
            value = self.cache.get(ref.num)
        self.cache[ref.num] = value
        return value

    def _object_stream(self, num):
        stream = self.get(Ref(num))
        raw = stream.data()
        n = int(self.get(stream.dict["N"]))
        first = int(self.get(stream.dict["First"]))
        head = Lexer(raw[:first])
        pairs = []
        for _ in range(n):
            obj_num = int(head.token())
            offset = int(head.token())
            pairs.append((obj_num, offset))
        out = {}
        for obj_num, offset in pairs:
            out[obj_num] = Parser(raw, first + offset, self).parse()
        return out

    # ---- pages
    def pages(self):
        root = self.get(self.trailer["Root"])
        node = self.get(root["Pages"])
        out = []
        self._walk(node, {}, out)
        return out

    INHERIT = ("Resources", "MediaBox", "CropBox", "Rotate")

    def _walk(self, node, inherited, out):
        node = self.get(node)
        if node is None:
            return
        passed = dict(inherited)
        for key in self.INHERIT:
            if key in node:
                passed[key] = node[key]
        if node.get("Type") == "Page":
            page = dict(node)
            for key, value in passed.items():
                page.setdefault(key, value)
            out.append(page)
            return
        for kid in node.get("Kids", []):
            self._walk(kid, passed, out)


# ---------------------------------------------------------------- writing

def serialise(value, remap):
    """PDF syntax for one value. Strings always go out as hex, which is safe."""
    if isinstance(value, Ref):
        return b"%d 0 R" % remap[value.num]
    if isinstance(value, Name):
        safe = re.sub(r"[^A-Za-z0-9._-]", lambda m: "#%02X" % ord(m.group(0)), value)
        return b"/" + safe.encode("latin-1")
    if isinstance(value, bool):
        return b"true" if value else b"false"
    if isinstance(value, int):
        return b"%d" % value
    if isinstance(value, float):
        return ("%g" % value).encode()
    if isinstance(value, bytes):
        return b"<" + value.hex().encode() + b">"
    if isinstance(value, list):
        return b"[" + b" ".join(serialise(v, remap) for v in value) + b"]"
    if isinstance(value, dict):
        return (b"<<" + b" ".join(serialise(Name(k), remap) + b" " + serialise(v, remap)
                                  for k, v in value.items()) + b">>")
    if isinstance(value, Stream):
        return serialise(value.dict, remap)
    if value is None:
        return b"null"
    return str(value).encode("latin-1")


def collect(doc, value, found, skip_keys=()):
    """Every object reachable from here, so a page brings its own furniture."""
    if isinstance(value, Ref):
        if value.num in found:
            return
        found.add(value.num)
        collect(doc, doc.get(value), found, skip_keys)
    elif isinstance(value, dict):
        for k, v in value.items():
            if k in skip_keys:
                continue
            collect(doc, v, found, skip_keys)
    elif isinstance(value, Stream):
        collect(doc, value.dict, found, skip_keys)
    elif isinstance(value, list):
        for v in value:
            collect(doc, v, found, skip_keys)


def write_pages(doc, indices, out_path):
    """Write the chosen pages (0-based) to a new PDF, copying objects as they are."""
    pages = doc.pages()
    chosen = [pages[i] for i in indices]

    found = set()
    for page in chosen:
        collect(doc, {k: v for k, v in page.items() if k != "Parent"}, found,
                skip_keys=("Parent",))

    # 1 = catalog, 2 = page tree, 3..n = the pages, then everything they use
    remap = {}
    next_num = 3 + len(chosen)
    for num in sorted(found):
        remap[num] = next_num
        next_num += 1

    out = bytearray(b"%PDF-1.6\n%\xe2\xe3\xcf\xd3\n")
    offsets = {}

    def put(num, body):
        offsets[num] = len(out)
        out.extend(b"%d 0 obj\n" % num + body + b"\nendobj\n")

    kids = b" ".join(b"%d 0 R" % (3 + i) for i in range(len(chosen)))
    put(1, b"<< /Type /Catalog /Pages 2 0 R >>")
    put(2, b"<< /Type /Pages /Count %d /Kids [%s] >>" % (len(chosen), kids))
    for i, page in enumerate(chosen):
        body = {k: v for k, v in page.items() if k != "Parent"}
        blob = serialise(body, remap)
        blob = b"<< /Parent 2 0 R " + blob[2:]     # every page points at the new tree
        put(3 + i, blob)
    for num in sorted(found):
        obj = doc.get(Ref(num))
        if isinstance(obj, Stream):
            body = dict(obj.dict)
            body["Length"] = len(obj.raw)
            put(remap[num], serialise(body, remap) + b"\nstream\n" + obj.raw + b"\nendstream")
        else:
            put(remap[num], serialise(obj, remap))

    highest = max(offsets)
    start = len(out)
    out.extend(b"xref\n0 %d\n0000000000 65535 f \n" % (highest + 1))
    for num in range(1, highest + 1):
        out.extend(b"%010d 00000 n \n" % offsets.get(num, 0))
    out.extend(b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n"
               % (highest + 1, start))
    with open(out_path, "wb") as fh:
        fh.write(bytes(out))
    return len(out)
