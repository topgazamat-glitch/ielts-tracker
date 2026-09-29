"""One of Azamat's Word booklets, as a handout that is done on a phone.

The design is his and is rendered as it is by booklet_html. What a handout
script adds is everything the paper leaves to a pen:

  - a box where the paper has only a dotted line, or nothing at all
    ("find and correct the mistake", "answer the questions");
  - how each box is answered on a phone: tap chips for a choice, a tick,
    a number pad, a growing box for a sentence of the student's own;
  - the answer each box wants, from his key, or None for the student's own
    words - saved and shown to him, never scored.

Every box on the page must be given a decision, or the build stops and
lists the ones left - a handout that marks a right answer wrong is worse
than one that does not mark at all.

    h = Handout(docx)
    h.item_box("1.3", 1, where="options")
    data = h.build(KEY, "Pre-Intermediate", 4, "Unit 4B & 4D - Celebrations")
"""
import html
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import booklet_html as bh        # noqa: E402

TAB = "<span class='tab'></span>"
ITEM_P = re.compile(r'(<p data-item="([0-9.]+):(\d+)"[^>]*>)(.*?)</p>', re.S)
LEADER_P = re.compile(r"<p[^>]*>" + re.escape(TAB) + r"</p>")
BLANK_TAG = re.compile(r'<input class="bk-blank" data-blank="(\d+)"[^>]*>')
SPOT = re.compile(r'<input class="bk-blank" data-blank="(\d+)"([^>]*)>'
                  r'|\{\{box:([0-9.]+):(\d+):([^:}]*):?([^}]*)\}\}')


def plain(fragment):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


ITEM_STYLE = 'style="margin-bottom:3.5px;line-height:1.25;padding-left:35px"'
NUM_SPAN = '<span style="color:#6E6E6E;font-size:10.5pt">%d  </span>'
TEXT_SPAN = '<span style="color:#1A1A1A;font-size:11.5pt">%s</span>'
PANEL = re.compile(
    r'(<table class="bk"><tr><td style="[^"]*background:#[0-9A-Fa-f]{6}[^"]*">'
    r'<table class="bk"><tr><td style="[^"]*background:#[0-9A-Fa-f]{6}[^"]*">)(.*?)(</td></tr></table>)'
    r'((?:(?!<table|</td></tr></table>).)*)(</td></tr></table>)', re.S)
DEEP_TEAL = "0B5456"


def told(line, bare=False):
    """One paragraph of an explanation, from **bold** / *italic* / [[RULE]]."""
    rule = re.match(r"^\[\[(.+?)\]\]\s*", line)
    lead = ""
    if rule:
        lead = ('<span style="font-weight:700;color:#%s">%s  </span>'
                % (DEEP_TEAL, html.escape(rule.group(1), quote=False)))
        line = line[rule.end():]
    num = re.match(r"^(\d+)\s+", line)
    if num and not rule:
        lead = '<span style="font-weight:700">%s  </span>' % num.group(1)
        line = line[num.end():]
    text = html.escape(line, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r'<span style="font-weight:700">\1</span>', text)
    text = re.sub(r"\*(.+?)\*", r'<span style="font-style:italic">\1</span>', text)
    return (lead + text) if bare else "<p>%s%s</p>" % (lead, text)


class Q:
    """What one box wants. answer=None is the student's own words."""

    def __init__(self, answer=None, options=None, control=None, labels=None):
        self.answer = answer
        self.options = options or []
        self.labels = labels or {}
        self.control = control


def choose(options, answer=None, labels=None):
    return Q(answer, options=options, labels=labels)


def tick(answer=None):
    return Q(answer, control="tick")


def own(control="long"):
    return Q(None, control=control)


def write(answer, control="long"):
    return Q(answer, control=control)


def note():
    """A box that may rightly stay empty - "correct the false ones" - so it
    is not counted as work left to do."""
    return Q(None, control="note")


def pair():
    """Work done in class - a survey, a partner's answers: saved if it is
    filled in, never holding a part back at home."""
    return Q(None, control="pair")


def number(answer):
    return Q(answer, control="number")


def fix(answer):
    """A sentence to correct - or, if it is already right, a tick."""
    return Q(answer, control="tickfill")


class Handout:
    def __init__(self, docx):
        self.html, self.blanks = bh.render(os.path.expanduser(docx), fillable=True)
        self.removed = set()
        self.hints = {}                     # blank index -> placeholder text
        self.texts = {}                     # (label, num) -> the item's words

    # ------------------------------------------------------------- placing
    def _token(self, label, num, width, placeholder=""):
        return "{{box:%s:%d:%s:%s}}" % (label, num, width, placeholder)

    def item_box(self, label, num, width="95%", where="first", placeholder=""):
        """A box at the end of one item: its first paragraph, the paragraph
        holding its A/B/C options, or where its dotted leader is."""
        paras = [m for m in ITEM_P.finditer(self.html)
                 if m.group(2) == label and int(m.group(3)) == num]
        if not paras:
            raise SystemExit("no item %s %d on the page" % (label, num))
        self.texts.setdefault((label, num), plain(paras[0].group(4)))
        if where == "first":
            m = paras[0]
        elif where == "options":
            m = next((p for p in paras if re.match(r"^A\s", plain(p.group(4)))), None)
            if m is None:
                raise SystemExit("no A/B options under %s %d" % (label, num))
        elif where == "leader":
            m = next((p for p in paras if p.group(4).rstrip().endswith(TAB)), paras[0])
        else:
            raise ValueError(where)
        guts = m.group(4)
        if guts.rstrip().endswith(TAB):
            guts = guts.rstrip()[:-len(TAB)]
        new = "%s%s %s</p>" % (m.group(1), guts, self._token(label, num, width, placeholder))
        self.html = self.html[:m.start()] + new + self.html[m.end():]

    def _instruction_end(self, label):
        i = self.html.find("%s  </span>" % label)
        if i < 0:
            raise SystemExit("no exercise %s" % label)
        return self.html.index("</p>", i) + 4

    def after_instruction(self, label, boxes):
        """Boxes on lines of their own under an exercise the paper leaves blank.
        boxes: [(num, lead_text, width, placeholder)]"""
        at = self._instruction_end(label)
        add = ""
        for num, lead, width, placeholder in boxes:
            self.texts[(label, num)] = lead or placeholder
            add += ('<p style="margin-bottom:6px">%s%s</p>'
                    % (("<b>%s</b> " % html.escape(lead)) if lead else "",
                       self._token(label, num, width, placeholder)))
        self.html = self.html[:at] + add + self.html[at:]

    def leaders(self, label, until, boxes):
        """The ruled lines under a writing task become `boxes`; the rest go.
        boxes: [(num, width, placeholder)]"""
        head = self.html.index("%s  </span>" % label)
        tail = self.html.index(until, head)
        part = self.html[head:tail]
        left = list(boxes)

        def line(m):
            if not left:
                return ""
            num, width, placeholder = left.pop(0)
            self.texts[(label, num)] = placeholder
            return '<p style="margin-bottom:8px">%s</p>' % self._token(label, num, width, placeholder)
        part = LEADER_P.sub(line, part)
        if left:
            raise SystemExit("not enough ruled lines under %s" % label)
        self.html = self.html[:head] + part + self.html[tail:]

    def one_per_line(self, start, until, at="box"):
        """Paper packs several short items into one line; a phone reads them
        better one to a line. at="box": each item starts with its box
        ("[ ] Invitation...  [ ] Would you like..."), so a new line goes before
        every box but the first. at="text": each item ends with its box
        ("A is from [ ]  B is from [ ]"), so a new line goes after each box."""
        a = self.html.rfind("<p", 0, self.html.index(start))
        b = self.html.index(until, a) if until else len(self.html)

        def para(m):
            body = m.group(2)
            tags = list(BLANK_TAG.finditer(body))
            cuts = []
            for k, t in enumerate(tags):
                before = plain(body[(tags[k - 1].end() if k else 0):t.start()])
                after = plain(body[t.end():(tags[k + 1].start() if k + 1 < len(tags) else len(body))])
                if at == "box" and k and before and after:
                    cuts.append(t.start())
                elif at == "text" and k + 1 < len(tags) and after:
                    cuts.append(t.end())
            for c in reversed(cuts):
                body = body[:c] + "<br>" + body[c:]
            return m.group(1) + body + "</p>"
        part = re.sub(r"(<p[^>]*>)(.*?)</p>", para, self.html[a:b], flags=re.S)
        self.html = self.html[:a] + part + self.html[b:]

    def can_do_grid(self, label):
        """The "I can... ☺ 😐 ☹" self-check: on paper three boxes a row, one to
        tick; on a phone one row of faces to tap. Returns (faces, [num per row])
        for the key; the second and third box of each row are gone."""
        head = self.html.index("%s  </span>" % label)
        a = self.html.index('<table class="bk">', head)
        b = self.html.index("</table>", a) + len("</table>")
        rows = re.findall(r"<tr>(.*?)</tr>", self.html[a:b], re.S)
        cells = [re.findall(r"(<td[^>]*>)(.*?)</td>", r, re.S) for r in rows]
        faces = [plain(c) for _o, c in cells[0][1:]]
        top_open, top = cells[0][0]
        out = ['<tr>%s%s</td></tr>' % (top_open.replace("<td", '<td colspan="2"', 1), top)]
        nums = []
        for k, row in enumerate(cells[1:], 1):
            (t_open, text), (b_open, box) = row[0], row[1]
            i = int(BLANK_TAG.search(box).group(1))
            self.blanks[i]["text"] = plain(text)
            nums.append(self.blanks[i]["num"])
            # one line between one can-do and the next, not between a can-do
            # and its own faces when a phone stacks them
            if k < len(cells) - 1:           # the last row keeps its closing rule
                t_open = re.sub(r"border-bottom:[^;\"]*", "border-bottom:0", t_open)
            b_open = re.sub(r"border-top:[^;\"]*", "border-top:0", b_open)
            out.append("<tr>%s%s</td>%s%s</td></tr>" % (t_open, text, b_open, box))
        self.html = self.html[:a] + '<table class="bk">' + "".join(out) + "</table>" + self.html[b:]
        return faces, nums

    def grid_rows(self, label, columns=None):
        """A table of boxes - things down the side, answers across - as one
        block per row: the row's name, then each box with its column's name.
        On a phone the table would otherwise stack into a list of loose boxes."""
        head = self.html.index("%s  </span>" % label)
        a = self.html.index('<table class="bk">', head)
        b = self.html.index("</table>", a) + len("</table>")
        rows = [re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)
                for r in re.findall(r"<tr>(.*?)</tr>", self.html[a:b], re.S)]
        names = columns if columns is not None else [plain(c) for c in rows[0][1:]]
        out = ""
        for k, row in enumerate(rows[1:], 1):
            bits = []
            for name, cell in zip(names, row[1:]):
                tag = BLANK_TAG.search(cell)
                if tag:                     # the teacher sees which row and column it was
                    self.blanks[int(tag.group(1))]["text"] = " ".join(
                        x for x in (plain(row[0]), name.rstrip(":")) if x)
                    box = re.sub(r' style="[^"]*"', "", tag.group(0))[:-1] + ' style="width:11em">'  # room for an answer
                    bits.append(('<span style="color:#6E6E6E">%s</span> ' % html.escape(name)
                                 if name else "") + box)
            out += ('<p data-item="%s:%d" style="margin-bottom:8px"><span style="font-weight:700">%s</span>'
                    '<br>%s</p>' % (label, k, html.escape(plain(row[0])), "<br>".join(bits)))
        self.html = self.html[:a] + out + self.html[b:]

    def retell(self, title, new_title, paragraphs):
        """An explanation box told again - in Uzbek, for a class that needs it.
        paragraphs use a small markup: **bold**, *italic*, [[NAME]] to start a
        rule, and {box} wherever one of the box's own answer boxes goes, in
        the order they were."""
        for m in PANEL.finditer(self.html):
            if plain(m.group(2)) != title:
                continue
            boxes = [t.group(0) for t in BLANK_TAG.finditer(m.group(4))]
            body = "".join(told(p) for p in paragraphs)
            for box in boxes:
                if "{box}" not in body:
                    raise SystemExit("the new %s has fewer boxes than the old" % title)
                body = body.replace("{box}", box, 1)
            if "{box}" in body:
                raise SystemExit("the new %s has more boxes than the old" % title)
            head = ('<p style="margin-bottom:0px"><span style="font-weight:700;color:#FFFFFF">%s</span></p>'
                    % html.escape(new_title))
            self.html = (self.html[:m.start()] + m.group(1) + head + m.group(3) + body
                         + m.group(5) + self.html[m.end():])
            return
        raise SystemExit("no box called %r" % title)

    def say_also(self, label, text, after=None):
        """The exercise's instruction once more, in Uzbek, on a line of its own
        under the English - under the paragraph holding `after`, if the
        instruction runs on to a second line."""
        at = self.html.index("%s  </span>" % label)
        start = self.html.rfind("<p", 0, at)
        if after:
            at = self.html.index(after, at)
        end = self.html.index("</p>", at) + len("</p>")
        style = re.match(r'<p[^>]*?( style="[^"]*")', self.html[start:end])
        line = '<p class="hx-uz" lang="uz"%s>%s</p>' % (style.group(1) if style else "",
                                                          told(text, bare=True))
        self.html = self.html[:end] + line + self.html[end:]

    def retell_cells(self, cells, after=None):
        """Table cells told again - the headings and the "Why" column of a
        table that explains. A cell is matched by what it says, since Word
        splits a cell's words across several pieces of formatting; each must
        be found exactly once - from `after` on, if a word like "Why" is also
        a cell in an earlier table."""
        start = self.html.index(after) if after else 0
        head, self.html = self.html[:start], self.html[start:]
        done = []

        def swap(m):
            text = plain(m.group(2))
            if text in cells:
                done.append(text)
                return '%s<p><span>%s</span></p></td>' % (m.group(1), cells[text])
            return m.group(0)
        self.html = head + re.sub(r"(<td[^>]*>)((?:(?!<td|<table).)*?)</td>", swap, self.html, flags=re.S)
        if sorted(done) != sorted(cells):
            twice = sorted({c for c in done if done.count(c) > 1})
            raise SystemExit("cells not found once each: missing %s, twice %s"
                             % (sorted(set(cells) - set(done)), twice))

    def goals(self, lines):
        """The "You will learn to" lines, told again."""
        at = self.html.index("You will learn to")
        end = self.html.index("</table>", at)
        part = self.html[at:end]
        old = [m for m in re.finditer(r"<p[^>]*>(.*?)</p>", part, re.S) if plain(m.group(1)).startswith("—")]
        if len(old) != len(lines):
            raise SystemExit("%d goals on the page, %d given" % (len(old), len(lines)))
        for m, line in reversed(list(zip(old, lines))):
            part = part[:m.start()] + '<p><span>—  </span>%s</p>' % told(line, bare=True) + part[m.end():]
        self.html = self.html[:at] + part + self.html[end:]

    # ---------------------------------------------------- shapes that recur
    def _items(self, label):
        return [m for m in ITEM_P.finditer(self.html) if m.group(2) == label]

    def options_on_lines(self, label):
        """A, B and C each on a line of their own, not run together in one line
        that wraps wherever the phone's width happens to fall."""
        for m in reversed(self._items(label)):
            guts = re.sub(r"(<span[^>]*>)([ABC])(</span>)", r"<br>\1\2\3", m.group(4))
            guts = re.sub(r"^<br>", "", guts)
            self.html = self.html[:m.start()] + m.group(1) + guts + "</p>" + self.html[m.end():]

    def odd_one_out(self, label, why="Why?"):
        """"Which word is different?": the item's words become the chips, and a
        box for why. Returns {item: [words]}; the key is (label, n, 1) for the
        word and (label, n, 2) for why."""
        def firsts():
            # only each item's own paragraph: Word sometimes tags a paragraph
            # further on - inside the next explanation box - with the same item
            seen, out = set(), []
            for m in self._items(label):
                if int(m.group(3)) not in seen and "·" in plain(m.group(4)):
                    seen.add(int(m.group(3)))
                    out.append(m)
            return out
        words = {int(m.group(3)): [w.strip() for w in re.sub(r"^\d+\s+", "", plain(m.group(4))).split("·")]
                 for m in firsts()}
        for n in sorted(words):
            self.item_box(label, n)
            self.item_box(label, n, placeholder=why)
        for m in reversed(firsts()):
            boxes = "".join(re.findall(r"\{\{box:[^}]*\}\}", m.group(4)))
            self.html = (self.html[:m.start()] + m.group(1) + NUM_SPAN % int(m.group(3)) + boxes
                         + "</p>" + self.html[m.end():])
        return words

    def sort_words(self, label, words, header_starts):
        """"Put the words in the groups": the word box and the empty group table
        become one line per word with the groups to tap. Returns the words in
        their numbered order; the key is (label, n, 1)."""
        head = self.html.index("%s  </span>" % label)
        t1 = self.html.index("<table", head)
        t2 = self.html.index("<table", self.html.index("</table>", t1))
        end = self.html.index("</table>", t2) + len("</table>")
        if not plain(self.html[t2:end]).startswith(header_starts):
            raise SystemExit("%s: the group table starts %r" % (label, plain(self.html[t2:end])[:40]))
        half = (len(words) + 1) // 2

        def cell(n):
            if n > len(words):
                return "<td></td>"
            self.texts[(label, n)] = words[n - 1]
            return ('<td style="vertical-align:top;border-top:0;border-bottom:0;border-left:0;border-right:0">'
                    '<p data-item="%s:%d" %s>%s%s</p></td>'
                    % (label, n, ITEM_STYLE, NUM_SPAN % n,
                       TEXT_SPAN % ("%s  {{box:%s:%d:60px:}}" % (words[n - 1], label, n))))
        rows = "".join("<tr>%s%s</tr>" % (cell(n), cell(n + half)) for n in range(1, half + 1))
        self.html = self.html[:t1] + '<table class="bk">' + rows + "</table>" + self.html[end:]
        return list(words)

    def key_first(self, label):
        """"Match the two halves": paper puts the halves side by side; a phone
        stacks them into one list alternating between the two. The endings go
        first, as a key; then each beginning, with the letters to tap."""
        head = self.html.index("%s  </span>" % label)
        a = self.html.index('<table class="bk">', head)
        b = self.html.index("</table>", a) + len("</table>")
        begin, ends = [], []
        for tr in re.findall(r"<tr>(.*?)</tr>", self.html[a:b], re.S):
            cells = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
            if len(cells) < 2 or not BLANK_TAG.search(cells[0]):
                continue
            n = int(re.search(r'data-item="[^:"]+:(\d+)"', cells[0]).group(1))
            begin.append((n, cells[0]))
            letter, rest = re.match(r"([a-z])\s+(.*)", plain(cells[1])).groups()
            ends.append((letter, rest))
        key = ('<table class="bk"><tr><td style="vertical-align:top;background:#F2F8F8;'
               'border-left:3px solid #127D80">'
               + "".join('<p style="margin:0"><span style="font-weight:700;color:#127D80">%s</span>  %s</p>'
                         % (l, html.escape(r, quote=False)) for l, r in sorted(ends))
               + "</td></tr></table>")
        self.html = self.html[:a] + key + "".join(c for _n, c in sorted(begin)) + self.html[b:]
        return [l for l, _r in sorted(ends)]

    def replace_para(self, containing, new):
        """Swap the whole paragraph that holds `containing` for `new`."""
        at = self.html.index(containing)
        start = self.html.rfind("<p", 0, at)
        end = self.html.index("</p>", at) + len("</p>")
        self.html = self.html[:start] + new + self.html[end:]

    def drop_blanks(self, indices):
        self.removed.update(indices)

    def replace(self, start, end, new):
        """Swap the markup from `start` up to and including `end` for `new`."""
        a = self.html.index(start)
        b = self.html.index(end, a) + len(end)
        self.html = self.html[:a] + new + self.html[b:]

    # --------------------------------------------------------------- build
    def build(self, key, level, number, title):
        questions, missing, seen = [], [], {}

        def spot(m):
            if m.group(1) is not None:
                i = int(m.group(1))
                if i in self.removed:
                    return ""
                b = self.blanks[i]
                label, num, rest, placeholder = b["label"], b["num"], m.group(2), self.hints.get(i, "")
                text = b["text"]
            else:
                label, num = m.group(3), int(m.group(4))
                rest = (' style="width:%s" autocomplete="off" autocapitalize="off"'
                        ' spellcheck="false"' % m.group(5))
                placeholder = m.group(6)
                text = self.texts.get((label, num), "")
            nth = seen[(label, num)] = seen.get((label, num), 0) + 1
            q = key.get((label, num, nth), "MISSING")
            if q == "MISSING":
                missing.append("%s item %s box %d  (%s)" % (label, num, nth, text[:50]))
                return m.group(0)
            if not isinstance(q, Q):
                q = Q(q) if q is not None else own(control=None)
            n = len(questions) + 1
            questions.append({
                "num": n, "kind": "typed" if q.answer else "open",
                "prompt": "%s  %s" % (label, re.sub(r"\s+", " ", text)[:160]),
                "answer": q.answer, "control": q.control,
                "options": [{"letter": o, "text": q.labels.get(o, "")} for o in q.options],
            })
            if placeholder:
                rest += ' placeholder="%s"' % html.escape(placeholder)
            return '<input class="bk-blank" data-q="%d"%s>' % (n, rest)

        layout = SPOT.sub(spot, self.html)
        if missing:
            raise SystemExit("no decision for:\n  " + "\n  ".join(missing))
        unused = [k for k in key if k[:2] not in seen or seen[k[:2]] < k[2]]
        if unused:
            raise SystemExit("decisions for boxes that are not there: %s" % unused)
        return {"level": level, "number": number, "title": title, "kind": "handout",
                "passages": {}, "layout": layout, "questions": questions}


def report(data):
    qs = data["questions"]
    for q in qs:
        how = ("chips " + "/".join(o["letter"] for o in q["options"])) if q["options"] \
            else (q["control"] or "gap")
        print("%-5s %3d  %-14s %-58s => %s" % ("MARK" if q["kind"] == "typed" else "", q["num"],
                                              how[:14], q["prompt"][:58], q["answer"]))
    marked = sum(1 for q in qs if q["kind"] == "typed")
    taps = sum(1 for q in qs if q["options"] or q["control"] == "tick")
    print("\nboxes: %d  (%d marked on the spot, %d tapped rather than typed, %d own words)"
          % (len(qs), marked, taps, len(qs) - marked))
