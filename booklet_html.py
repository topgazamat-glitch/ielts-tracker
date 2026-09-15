"""Render one of the booklets as a web page, the way it looks on paper.

The point is that a student opens their booklet on screen and sees their
booklet - the teal rules, the pale exercise boxes, the key-word panels, the
reading passages - rather than a list of questions with the design thrown
away.

    python3 booklet_html.py "I10AC Opportunities — BOOKLET.docx" --out out.html

Word carries this design in direct formatting rather than named styles, so
this reads the run properties themselves: bold, italic, colour, size, and for
tables the cell fill and borders. No images appear in any of the booklets,
which is what makes a faithful copy possible without a Word library.
"""
import argparse
import html
import os
import re
import sys
import zipfile

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

RUN = re.compile(r"<w:r\b[^>]*/>|<w:r\b.*?</w:r>", re.S)


def elements(xml, *names):
    """Every top-level <w:name> ... </w:name> in document order.

    A regex cannot do this. The booklets nest a table inside a table cell -
    the terracotta ERROR WARNING chip sits in a cell of the box that holds it -
    and `<w:tc>.*?</w:tc>` closes the outer cell at the inner one's end tag,
    which silently flattened those boxes into a single pale rectangle with
    white text on it. So the tags are counted rather than matched.
    """
    want = "|".join(names)
    token = re.compile(r"<w:(%s)\b([^>]*)>|</w:(%s)>" % (want, want))
    out, depth, start = [], 0, None
    for m in token.finditer(xml):
        if m.group(1) is not None:            # an opening tag
            if m.group(2).endswith("/"):      # ... that closes itself
                if depth == 0:
                    out.append(m.group(0))
                continue
            if depth == 0:
                start = m.start()
            depth += 1
        else:
            depth -= 1
            if depth == 0 and start is not None:
                out.append(xml[start:m.end()])
                start = None
    return out


def text_of(run):
    """Everything the run prints, tabs and breaks included."""
    out = []
    for m in re.finditer(r"<w:t[^>]*>(.*?)</w:t>|<w:tab/>|<w:br/>", run, re.S):
        if m.group(0).startswith("<w:tab"):
            out.append("\t")
        elif m.group(0).startswith("<w:br"):
            out.append("\n")
        else:
            out.append(html.unescape(m.group(1)))
    return "".join(out)


def on(q, name):
    """Is this toggle actually on?

    Word writes the switch-off as an element too - <w:b w:val="0"/> means *not*
    bold - so presence is not the question. Reading presence alone set every
    run in the booklet bold, italic, capitalised and struck through at once.
    """
    m = re.search(r'<w:%s\b([^>]*)>' % name, q)
    if not m:
        return False
    val = re.search(r'w:val="([^"]+)"', m.group(1))
    return not val or val.group(1) not in ("0", "false", "off", "none")


def run_style(run):
    pr = re.search(r"<w:rPr>(.*?)</w:rPr>", run, re.S)
    if not pr:
        return ""
    q, css = pr.group(1), []
    if on(q, "b"):
        css.append("font-weight:700")
    if on(q, "i"):
        css.append("font-style:italic")
    if on(q, "u"):
        css.append("text-decoration:underline")
    if on(q, "strike"):
        css.append("text-decoration:line-through")
    c = re.search(r'<w:color w:val="([0-9A-Fa-f]{6})"', q)
    if c and c.group(1).lower() != "auto":
        css.append("color:#" + c.group(1))
    sz = re.search(r'<w:sz w:val="(\d+)"', q)
    if sz:
        # Word counts half-points; the booklets run 8pt to 20pt
        css.append("font-size:%gpt" % (int(sz.group(1)) / 2.0))
    hl = re.search(r'<w:highlight w:val="([a-z]+)"', q)
    if hl and hl.group(1) != "none":
        css.append("background:%s" % hl.group(1))
    sp = re.search(r'<w:spacing w:val="(-?\d+)"', q)
    if sp:
        css.append("letter-spacing:%gpx" % (int(sp.group(1)) / 20.0))
    if on(q, "caps"):
        css.append("text-transform:uppercase")
    if on(q, "smallCaps"):
        css.append("font-variant:small-caps")
    return ";".join(css)


ALIGN = {"center": "center", "right": "right", "both": "justify",
         "left": "left", "start": "left", "end": "right"}


def para_style(p):
    pr = re.search(r"<w:pPr>(.*?)</w:pPr>", p, re.S)
    css = []
    if pr:
        q = pr.group(1)
        jc = re.search(r'<w:jc w:val="(\w+)"', q)
        if jc and jc.group(1) in ALIGN:
            css.append("text-align:" + ALIGN[jc.group(1)])
        sp = re.search(r"<w:spacing\b([^/>]*)/?>", q)
        if sp:
            before = re.search(r'w:before="(\d+)"', sp.group(1))
            after = re.search(r'w:after="(\d+)"', sp.group(1))
            line = re.search(r'w:line="(\d+)"', sp.group(1))
            if before:
                css.append("margin-top:%gpx" % (int(before.group(1)) / 20.0))
            if after:
                css.append("margin-bottom:%gpx" % (int(after.group(1)) / 20.0))
            if line and "auto" not in sp.group(1):
                css.append("line-height:%g" % (int(line.group(1)) / 240.0))
        ind = re.search(r"<w:ind\b([^/>]*)/?>", q)
        if ind:
            left = re.search(r'w:(?:left|start)="(\d+)"', ind.group(1))
            if left:
                css.append("padding-left:%gpx" % (int(left.group(1)) / 20.0))
        shd = re.search(r'<w:shd[^>]*w:fill="([0-9A-Fa-f]{6})"', q)
        if shd:
            css.append("background:#" + shd.group(1))
        bdr = re.search(r"<w:pBdr>(.*?)</w:pBdr>", q, re.S)
        if bdr:
            for side in ("top", "bottom", "left", "right"):
                b = re.search(r'<w:%s\b([^/>]*)/?>' % side, bdr.group(1))
                if not b or 'w:val="nil"' in b.group(1) or 'w:val="none"' in b.group(1):
                    continue
                col = re.search(r'w:color="([0-9A-Fa-f]{6})"', b.group(1))
                size = re.search(r'w:sz="(\d+)"', b.group(1))
                px = max(1, round(int(size.group(1)) / 8.0)) if size else 1
                css.append("border-%s:%dpx solid #%s"
                           % (side, px, col.group(1) if col else "999999"))
    return ";".join(css)


BLANK = re.compile("[\u2026]{2,}|\\.{4,}|_{3,}")
LABEL_AT = re.compile(r"^\s*(\d+\.\d+)\b")
ITEM_AT = re.compile(r"^\s*(\d+)\s")


class Ctx:
    """Where in the booklet we are, so a blank knows which answer is its own.

    The booklet numbers itself - "1.2" for the exercise, then "1", "2", "3"
    for the items inside it - and the answer key is written the same way. A
    blank therefore belongs to whichever exercise and item last went past,
    which is what joins the printed page to the marking.
    """

    def __init__(self, fillable=False):
        self.fillable = fillable
        self.label = None
        self.num = None
        self.seen = 0          # blanks so far inside this item
        self.blanks = []       # (label, num, ordinal within the item, text)
        self.loose = {}        # label -> blanks seen in it with no item number
        self.text = ""

    def enter(self, plain):
        m = LABEL_AT.match(plain)
        if m:
            self.label, self.num, self.seen = m.group(1), None, 0
            self.loose.pop(m.group(1), None)
            self.text = plain.strip()
            return
        m = ITEM_AT.match(plain)
        if m and self.label:
            self.num, self.seen = int(m.group(1)), 0
            self.text = plain.strip()

    def blank(self, dots):
        if not self.fillable or self.label is None:
            return None
        num, nth = self.num, self.seen + 1
        if num is None:
            # Some exercises are a conversation or an advert rather than a
            # numbered list, so the page has no "1", "2", "3" to hang the key
            # on. The key numbers them anyway, in the order they are read, so
            # the blanks are counted the same way.
            self.loose[self.label] = self.loose.get(self.label, 0) + 1
            num, nth = self.loose[self.label], 1
        self.seen += 1
        self.blanks.append({"label": self.label, "num": num,
                            "nth": nth, "text": self.text})
        return len(self.blanks) - 1


def render_runs(container, ctx=None):
    out = []
    for m in RUN.finditer(container):
        run = m.group(0)
        t = text_of(run)
        if not t:
            continue
        style = run_style(run)
        pieces, last = [], 0
        for b in BLANK.finditer(t) if ctx else []:
            pieces.append(html.escape(t[last:b.start()]))
            idx = ctx.blank(b.group(0))
            if idx is None:
                pieces.append(html.escape(b.group(0)))
            else:
                # as wide as the space the paper gave it, within reason
                w = min(max(len(b.group(0)) * 9 + 20, 60), 260)
                pieces.append('<input class="bk-blank" data-blank="%d" '
                              'style="width:%dpx" autocomplete="off" '
                              'autocapitalize="off" spellcheck="false">'
                              % (idx, w))
            last = b.end()
        pieces.append(html.escape(t[last:]))
        esc = "".join(pieces)
        esc = esc.replace("\t", "<span class='tab'></span>").replace("\n", "<br>")
        out.append(f'<span style="{style}">{esc}</span>' if style else esc)
    return "".join(out)


def cell_style(tc):
    pr = re.search(r"<w:tcPr>(.*?)</w:tcPr>", tc, re.S)
    css = ["vertical-align:top"]
    if pr:
        q = pr.group(1)
        shd = re.search(r'<w:shd[^>]*w:fill="([0-9A-Fa-f]{6})"', q)
        if shd and shd.group(1).lower() != "auto":
            css.append("background:#" + shd.group(1))
        wd = re.search(r'<w:tcW w:w="(\d+)" w:type="dxa"', q)
        if wd:
            css.append("width:%gpx" % (int(wd.group(1)) / 20.0))
        bdrs = re.search(r"<w:tcBorders>(.*?)</w:tcBorders>", q, re.S)
        any_border = False
        if bdrs:
            for side in ("top", "bottom", "left", "right"):
                b = re.search(r'<w:%s\b([^/>]*)/?>' % side, bdrs.group(1))
                if not b:
                    continue
                if 'w:val="nil"' in b.group(1) or 'w:val="none"' in b.group(1):
                    css.append("border-%s:0" % side)
                    continue
                col = re.search(r'w:color="([0-9A-Fa-f]{6})"', b.group(1))
                size = re.search(r'w:sz="(\d+)"', b.group(1))
                px = max(1, round(int(size.group(1)) / 8.0)) if size else 1
                css.append("border-%s:%dpx solid #%s"
                           % (side, px, col.group(1) if col else "999999"))
                any_border = True
        if not any_border and not bdrs:
            css.append("border:0")
        mar = re.search(r"<w:tcMar>(.*?)</w:tcMar>", q, re.S)
        if mar:
            for side, prop in (("top", "top"), ("bottom", "bottom"),
                               ("left", "left"), ("right", "right")):
                m = re.search(r'<w:%s w:w="(\d+)"' % side, mar.group(1))
                if m:
                    css.append("padding-%s:%gpx" % (prop, int(m.group(1)) / 20.0))
    return ";".join(css)


def render_table(tbl, ctx=None):
    inner = tbl[tbl.index(">") + 1:tbl.rindex("</w:tbl>")]
    out = ['<table class="bk">']
    for tr in elements(inner, "tr"):
        out.append("<tr>")
        body = tr[tr.index(">") + 1:tr.rindex("</w:tr>")]
        for tc in elements(body, "tc"):
            span = re.search(r'<w:gridSpan w:val="(\d+)"', tc)
            attr = f' colspan="{span.group(1)}"' if span else ""
            out.append(f'<td{attr} style="{cell_style(tc)}">')
            guts = tc[tc.index(">") + 1:tc.rindex("</w:tc>")]
            out.append(render_blocks(guts, ctx))
            out.append("</td>")
        out.append("</tr>")
    out.append("</table>")
    return "".join(out)


def plain_text(block):
    return "".join(text_of(m.group(0)) for m in RUN.finditer(block))


def render_blocks(container, ctx=None):
    out = []
    for block in elements(container, "tbl", "p"):
        if block.startswith("<w:tbl"):
            out.append(render_table(block, ctx))
            continue
        if ctx:
            ctx.enter(plain_text(block))
        inner = render_runs(block, ctx)
        style = para_style(block)
        if not inner.strip():
            out.append(f'<p class="sp" style="{style}"></p>' if style
                       else '<p class="sp"></p>')
        else:
            out.append(f'<p style="{style}">{inner}</p>' if style
                       else f"<p>{inner}</p>")
    return "".join(out)


PAGE_CSS = """
.booklet { --ink:#1A1A1A; --teal:#127D80; --deep:#0B5456; --soft:#F2F8F8;
  color:var(--ink); font-family:'Segoe UI',-apple-system,BlinkMacSystemFont,
  'Helvetica Neue',Arial,sans-serif; line-height:1.5; }
.booklet p { margin:0 0 6px; }
.booklet p.sp { margin:0; height:8px; }
.booklet table.bk { border-collapse:collapse; width:100%; margin:10px 0;
  table-layout:fixed; }
.booklet table.bk td { padding:8px 10px; word-wrap:break-word; }
.booklet .tab { display:inline-block; width:22px; }
.booklet table.bk table.bk { margin:0; }
.booklet .bk-blank { font:inherit; color:#0B5456; background:#F2F8F8;
  border:0; border-bottom:1.5px solid #9CC; border-radius:3px 3px 0 0;
  padding:1px 6px; min-height:24px; }
.booklet .bk-blank:focus { outline:0; background:#E6F2F2;
  border-bottom-color:#127D80; }
.booklet .bk-blank.right { background:#E7F6EC; border-bottom-color:#2E9E5B; }
.booklet .bk-blank.wrong { background:#FDECEC; border-bottom-color:#D35; }
.booklet .bk-was { color:#2E9E5B; font-weight:600; white-space:nowrap; }
"""


def render(path, fillable=False):
    xml = zipfile.ZipFile(os.path.expanduser(path)).read(
        "word/document.xml").decode("utf-8", "replace")
    body = xml.split("<w:body>", 1)[1].rsplit("</w:body>", 1)[0]
    body = re.sub(r"<w:sectPr\b.*?</w:sectPr>", "", body, flags=re.S)
    ctx = Ctx(fillable) if fillable else None
    inner = render_blocks(body, ctx)
    return f'<div class="booklet">{inner}</div>', (ctx.blanks if ctx else [])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("booklet")
    ap.add_argument("--out", default="booklet.html")
    args = ap.parse_args()
    inner, blanks = render(args.booklet, fillable=True)
    print("%d blanks a student can type in" % len(blanks))
    title = os.path.basename(args.booklet).split("—")[0].strip()
    open(args.out, "w").write(
        "<!doctype html><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{html.escape(title)}</title><style>"
        "body{margin:0;background:#f4f4f6}"
        ".sheet{max-width:820px;margin:24px auto;background:#fff;padding:36px 40px;"
        "box-shadow:0 1px 3px rgba(0,0,0,.12);border-radius:4px}"
        + PAGE_CSS + f"</style><div class='sheet'>{inner}</div>")
    print(args.out, len(inner), "bytes of booklet")


if __name__ == "__main__":
    main()


# ------------------------------------------------ joining page to answer key

def split_for(answer, n):
    """One key answer, n blanks on the page.

    An item with two gaps carries both answers in one line of the key -
    "heat / melts", "was / were, would definitely do" - which is unusable as a
    single box but exactly right once the sentence has two boxes in it. The
    comma is tried first because a slash can belong inside one of the halves.
    """
    if n == 1:
        return [answer]
    for sep in (",", "/"):
        parts = [p.strip() for p in answer.split(sep)]
        if len(parts) == n and all(parts):
            return parts
    return None


def to_test(booklet, key_path, level, title, number=1):
    """A fillable booklet plus the questions the key can mark."""
    import convert_booklet as cb
    inner, blanks = render(booklet, fillable=True)
    key = cb.read_key(key_path)

    # how many blanks each item has, so a two-gap sentence is recognised
    counts = {}
    for b in blanks:
        counts[(b["label"], b["num"])] = counts.get((b["label"], b["num"]), 0) + 1

    questions, layout, unmarked = [], inner, 0
    for i, b in enumerate(blanks):
        answers = key.get(b["label"]) or {}
        want = answers.get(b["num"])
        parts = split_for(cb.tidy_answer(want), counts[(b["label"], b["num"])]) \
            if want else None
        chosen = parts[b["nth"] - 1] if parts else None
        markable = bool(chosen) and cb.typeable(chosen, prompt="")
        if not markable:
            unmarked += 1
        # every blank becomes a question, so everything the student types is
        # kept; the ones the key cannot judge are "open" and score nothing
        questions.append({"num": len(questions) + 1,
                          "kind": "typed" if markable else "open",
                          "prompt": "%s  %s" % (b["label"], b["text"][:160]),
                          "answer": chosen if markable else None,
                          "options": [], "blank": i})
    # the layout points at its questions by number, so the page can put the
    # student's own box back in the right hole
    for q in questions:
        layout = layout.replace('data-blank="%d"' % q["blank"],
                                'data-q="%d"' % q["num"])
    for q in questions:
        q.pop("blank", None)
    return {"level": level, "number": number, "title": title,
            "passages": {}, "layout": layout, "questions": questions}, unmarked
