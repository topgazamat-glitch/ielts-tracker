"""Apply Azamat's own handout redesign to the other booklets.

He reworked the Unit 9 and 10 Intermediate handouts in Word himself. Three
changes ran through all of them, and this repeats exactly those:

  1. the Name / Class / Date line on the cover goes; "Prepared by" stays
  2. a multiple-choice question keeps its line, and its A / B / C options
     move to a line of their own underneath, with the same indent
  3. a question answered on a dotted line keeps its line, and the dotted
     line moves underneath it, the full width, with room to write

Nothing is reworded and nothing else moves. It works on the Word XML
directly, so fonts, colours, boxes and spacing stay exactly as they were.

    python3 handouts/apply_design.py in.docx out.docx
"""
import re
import sys
import zipfile
from xml.dom import minidom

RUN = re.compile(r"<w:r>.*?</w:r>|<w:r [^>]*>.*?</w:r>", re.S)
PARA = re.compile(r"<w:p>.*?</w:p>|<w:p [^>]*>.*?</w:p>", re.S)
TEXT = re.compile(r"<w:t(?:\s[^>]*)?>(.*?)</w:t>", re.S)


def run_text(r):
    return "".join(TEXT.findall(r))


def ppr_of(p):
    m = re.search(r"<w:pPr>.*?</w:pPr>", p, re.S)
    return m.group(0) if m else ""


def plain(p):
    return "".join(run_text(r) for r in RUN.findall(p))


def is_bold(r):
    m = re.search(r"<w:b(/>| [^>]*>)", r)
    if not m:
        return False
    v = re.search(r'w:val="([^"]+)"', m.group(0))
    return not v or v.group(1) not in ("false", "0", "off")


def para(ppr, runs, attrs=""):
    return "<w:p%s>%s%s</w:p>" % (attrs, ppr, "".join(runs))


def drop_name_line(p):
    """Change 1: keep only the tab and 'Prepared by …'."""
    t = plain(p)
    if not ("Name" in t and "Class" in t and "Date" in t and "Prepared by" in t):
        return None
    runs = RUN.findall(p)
    keep, seen_tab = [], False
    for r in runs:
        txt = run_text(r)
        if "\t" in txt or "<w:tab/>" in r:
            seen_tab = True
        if seen_tab:
            keep.append(r)
    if not keep:
        return None
    head = p[:p.index(runs[0])] if runs else p
    return head + "".join(keep) + "</w:p>"


def split_mcq(p):
    """Change 2: options under the question."""
    runs = RUN.findall(p)
    if len(runs) < 4 or not re.match(r"^\s*\d+\s*$", run_text(runs[0])):
        return None
    letters = [(i, run_text(r).strip()) for i, r in enumerate(runs)
               if is_bold(r) and run_text(r).strip() in ("A", "B", "C", "D")]
    order = [l for _i, l in letters]
    if order[:3] != ["A", "B", "C"]:
        return None
    cut = letters[0][0]
    if cut < 2:                        # nothing before the options: not a question
        return None
    ppr = ppr_of(p)
    first = para(ppr, runs[:cut])
    second = para(ppr, runs[cut:])
    return first + second


def split_answer_line(p):
    """Change 3: the dotted answer line goes under the question."""
    ppr = ppr_of(p)
    if 'w:leader="dot"' not in ppr:
        return None
    runs = RUN.findall(p)
    if len(runs) < 2 or run_text(runs[-1]) != "\t":
        return None
    q = "".join(run_text(r) for r in runs[:-1]).strip()
    body = re.sub(r"^\d+\s+", "", q)
    # a real question, not a short label such as "Speaker 1" or "Name"
    if not (body.endswith("?") or len(body) >= 40):
        return None
    tab_run = runs[-1]
    ppr_q = re.sub(r"<w:tabs>.*?</w:tabs>", "", ppr, flags=re.S)
    ind = re.search(r'<w:ind [^>]*w:left="(\d+)"', ppr)
    left = ind.group(1) if ind else "0"
    ppr_line = ('<w:pPr><w:tabs><w:tab w:val="right" w:pos="9160" '
                'w:leader="dot"/></w:tabs><w:spacing w:after="255"/>'
                '<w:ind w:left="%s"/></w:pPr>' % left)
    return para(ppr_q, runs[:-1]) + para(ppr_line, [tab_run])


NAME_TABLE = re.compile(r"<w:tbl>(?:(?!<w:tbl>).)*?</w:tbl>", re.S)


def drop_name_table(xml):
    """Change 1, cover-page style: the three ruled boxes NAME / CLASS / DATE."""
    n = 0

    def one(m):
        nonlocal n
        cells = [re.sub(r"<[^>]+>", "", c).strip().upper()
                 for c in re.findall(r"<w:tc>.*?</w:tc>", m.group(0), re.S)]
        if cells == ["NAME", "CLASS", "DATE"]:
            n += 1
            return ""
        return m.group(0)
    return NAME_TABLE.sub(one, xml), n


def transform(xml):
    counts = {"name line": 0, "options": 0, "answer lines": 0}
    xml, counts["name line"] = drop_name_table(xml)

    def one(m):
        p = m.group(0)
        for key, fn in (("name line", drop_name_line), ("options", split_mcq),
                        ("answer lines", split_answer_line)):
            out = fn(p)
            if out:
                counts[key] += 1
                return out
        return p
    return PARA.sub(one, xml), counts


def words_of(xml):
    t = " ".join(TEXT.findall(xml))
    return sorted(re.sub(r"[\t\s]+", " ", t).split())


def apply(src, dest):
    zin = zipfile.ZipFile(src)
    doc = zin.read("word/document.xml").decode("utf-8")
    new, counts = transform(doc)
    minidom.parseString(new.encode("utf-8"))          # must still be valid XML
    before, after = words_of(doc), words_of(new)
    removed = list(before)
    for w in after:
        removed.remove(w)                             # raises if a word appeared
    gone = [w for w in removed if w.upper() not in
            ("NAME", "CLASS", "DATE") and not re.fullmatch(r"…+", w)]
    if gone:
        raise ValueError("words would be lost: %s" % gone[:10])
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = new.encode("utf-8") if item.filename == "word/document.xml" \
                else zin.read(item.filename)
            zout.writestr(item, data)
    return counts


if __name__ == "__main__":
    print(apply(sys.argv[1], sys.argv[2]))
