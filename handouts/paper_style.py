"""Azamat's paper handouts, dressed like the website.

The booklets are Word files in teal: section bars, exercise numbers, the
boxes that explain. The website draws the same booklets in its own clothes -
plum, the explanation boxes as cards coloured by what they are (blue for
listening and sound, gold for a checklist, rose for a warning), the box's
name as coloured capitals rather than a filled tag, and a deep plum band for
the title. This does the same to the Word file, and only that: every word,
box, table and page break stays where it was. Calibri becomes Aptos (Word's
own font, a little closer to the site's) at 96% of the size, which fills a
line the same way; the cover title is Georgia.

    python3 handouts/paper_style.py in.docx out.docx        one file
    python3 handouts/paper_style.py --all [--pdf]           every paper handout on the Desktop

--all reads ~/Desktop/Handouts and writes the same folders under
~/Desktop/Handouts (website style); nothing in the original folder changes.
--pdf also has Word print each one, and says if a handout's page count moved.
"""
import glob
import os
import re
import subprocess
import sys
import zipfile

from lxml import etree

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = "{%s}" % W_NS
NS = {"w": W_NS}

# the site's colours (static/style.css, the handout sheet)
PLUM, DEEP, INK, INK3 = "701589", "320A3E", "1C0F22", "857A8C"
SOFT, SOFT2, CHIP, LINE = "F5EDF8", "FBF8FC", "D9C2E2", "E1D6E8"
HERO, GOLD = "2A0736", "FFD36E"

# teal to plum, everywhere a colour is named
COLOURS = {
    "127D80": PLUM, "0B5456": DEEP, "E8F1F1": SOFT, "F2F8F8": SOFT2, "AECFD0": CHIP,
    "1A1A1A": INK, "6E6E6E": INK3, "C9C9C9": LINE, "D8D8D8": LINE,
    "C0745F": "B8283A", "FBF0EE": "FFF1F2",
    "2E74B5": PLUM, "1F4D78": DEEP,           # Word's own heading colours, in the styles
}
FONTS = {"Calibri": "Aptos", "Verdana": "Aptos", "Cambria": "Georgia"}
# Aptos is about 4% wider than Calibri and has taller small letters, so at 96%
# of the size a line holds the same words and reads just as large - and every
# page ends where it did.
SCALE = 0.96

# a box, by what it is: (fill, border, name and numbers, rule names)
KINDS = {
    "learn":  (SOFT2, CHIP, PLUM, DEEP),
    "words":  (SOFT2, CHIP, PLUM, DEEP),
    "text":   (SOFT2, CHIP, PLUM, DEEP),
    "warn":   ("FFF1F2", "F2B8C1", "B8283A", "B8283A"),
    "listen": ("EEF6FD", "BFDAF1", "0B69AD", "0A4F82"),
    "check":  ("FFF8E3", "EDD58A", "6B4B00", "6B4B00"),
}
TEALS = {"127D80", "C0745F"}


def text_of(el):
    return "".join(el.itertext()).strip()


def kind_of(title, tag_fill):
    t = title.upper()
    if tag_fill == "C0745F":
        return "warn"
    if t.startswith("CHECK") or "TEKSHIR" in t:
        return "check"
    if "KEY WORD" in t or "KALIT SO" in t:
        return "words"
    if any(w in t for w in ("PRONUNCIATION", "HEAR", "LISTEN", "TALAFFUZ", "ESHIT", "TINGLA")):
        return "listen"
    return "learn"


def shd(tc):
    s = tc.find("w:tcPr/w:shd", NS)
    return s.get(W + "fill", "").upper() if s is not None else ""


def set_colour(run_parent, old, new):
    for c in run_parent.iter(W + "color"):
        if c.get(W + "val", "").upper() in old:
            c.set(W + "val", new)


def box_tag(cell):
    """A box's name: a small table with a teal cell (the booklets now), or a
    paragraph shaded teal (the older ones). Returns (element, its shading)."""
    tag = cell.find("w:tbl", NS)
    if tag is not None:
        tag_cells = tag.findall("w:tr/w:tc", NS)
        if len(tag_cells) == 1 and shd(tag_cells[0]) in TEALS:
            return tag, tag_cells[0].find("w:tcPr/w:shd", NS)
        return None, None
    first = cell.find("w:p", NS)
    s = first.find("w:pPr/w:shd", NS) if first is not None else None
    if s is not None and s.get(W + "fill", "").upper() in TEALS and text_of(first):
        return first, s
    # the newest: a tinted box whose first line is its name in coloured capitals
    if first is not None and shd(cell) in ("F2F8F8", "FBF0EE", "E8F1F1"):
        name = text_of(first)
        c = first.find("w:r/w:rPr/w:color", NS)
        colour = c.get(W + "val", "").upper() if c is not None else ""
        if name and name == name.upper() and len(name) <= 60 and colour in ("0B5456", "127D80", "C0745F"):
            return first, etree.Element(W + "shd", {W + "fill": "C0745F" if colour == "C0745F" else "127D80"})
    return None, None


def dress_boxes(body):
    """Each explanation box in its own colours; its name as coloured capitals."""
    done = 0
    for tbl in body.iter(W + "tbl"):
        cells = tbl.findall("w:tr/w:tc", NS)
        if len(cells) != 1:
            continue
        cell = cells[0]
        tag, tag_shd = box_tag(cell)
        if tag is None:
            continue
        fill, line, accent, deep = KINDS[kind_of(text_of(tag), tag_shd.get(W + "fill", "").upper())]
        pr = cell.find("w:tcPr", NS)
        for b in pr.iterfind("w:tcBorders/*", NS):
            if b.get(W + "val") not in (None, "none", "nil"):
                b.set(W + "color", line)
        s = pr.find("w:shd", NS)
        if s is not None:
            s.set(W + "fill", fill)
        # the name: no filled tag, the box's colour on its own ground
        tag_shd.set(W + "fill", fill)
        set_colour(tag, {"FFFFFF", "0B5456", "127D80", "C0745F"}, accent)
        # inside: the teal numbers and rule names take the box's colours
        for child in cell:
            if child is tag:
                continue
            set_colour(child, {"127D80"}, accent)
            set_colour(child, {"0B5456"}, deep)
        done += 1
    return done


def ppr(p):
    pr = p.find("w:pPr", NS)
    if pr is None:
        pr = etree.Element(W + "pPr")
        p.insert(0, pr)
    return pr


def dress_cover(body):
    """The first three lines - unit, title, lessons - as the site's plum band:
    one shaded cell holding them, a little wider than the text so the words
    stay exactly where they were."""
    paras = []
    for el in body:
        if el.tag != W + "p" or len(paras) == 3:
            break
        paras.append(el)
    if len(paras) < 2:
        return False
    kicker, title = paras[:2]
    big = [int(s.get(W + "val")) for s in title.iter(W + "sz") if s.get(W + "val", "").isdigit()]
    if not big or max(big) < 34 or not text_of(kicker).upper().startswith("UNIT"):
        return False
    width = body.find("w:sectPr/w:pgSz", NS)
    margins = body.find("w:sectPr/w:pgMar", NS)
    text_w = 9360
    if width is not None and margins is not None:
        text_w = int(width.get(W + "w")) - int(margins.get(W + "left")) - int(margins.get(W + "right"))
    bleed = 150
    tbl = etree.Element(W + "tbl")
    tpr = etree.SubElement(tbl, W + "tblPr")
    etree.SubElement(tpr, W + "tblW", {W + "type": "dxa", W + "w": str(text_w + 2 * bleed)})
    etree.SubElement(tpr, W + "tblInd", {W + "type": "dxa", W + "w": str(-bleed)})
    borders = etree.SubElement(tpr, W + "tblBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        etree.SubElement(borders, W + side, {W + "val": "nil"})
    etree.SubElement(tpr, W + "tblLayout", {W + "type": "fixed"})
    grid = etree.SubElement(tbl, W + "tblGrid")
    etree.SubElement(grid, W + "gridCol", {W + "w": str(text_w + 2 * bleed)})
    tc = etree.SubElement(etree.SubElement(tbl, W + "tr"), W + "tc")
    tcpr = etree.SubElement(tc, W + "tcPr")
    etree.SubElement(tcpr, W + "tcW", {W + "type": "dxa", W + "w": str(text_w + 2 * bleed)})
    etree.SubElement(tcpr, W + "shd", {W + "val": "clear", W + "color": "auto", W + "fill": HERO})
    mar = etree.SubElement(tcpr, W + "tcMar")
    for side, v in (("top", 110), ("left", bleed), ("bottom", 110), ("right", bleed)):
        etree.SubElement(mar, W + side, {W + "type": "dxa", W + "w": str(v)})
    kicker.addprevious(tbl)
    band = paras[:3]
    for p in band:
        for old in ppr(p).findall("w:pBdr", NS):
            ppr(p).remove(old)
        tc.append(p)
    spacing = ppr(band[-1]).find("w:spacing", NS)
    if spacing is not None:
        spacing.set(W + "after", "0")
    for p in band:
        for r in p.findall("w:r", NS):
            rpr = r.find("w:rPr", NS)
            if rpr is None:
                rpr = etree.Element(W + "rPr")
                r.insert(0, rpr)
            c = rpr.find("w:color", NS)
            was = c.get(W + "val", "").upper() if c is not None else ""
            sizes = [int(x.get(W + "val")) for x in rpr.iter(W + "sz") if x.get(W + "val", "").isdigit()]
            if p is kicker:
                now = GOLD if was == "127D80" else CHIP
            elif sizes and max(sizes) >= 34:
                now = "FFFFFF"            # the title, in the site's serif
                f = rpr.find("w:rFonts", NS)
                if f is None:
                    f = etree.Element(W + "rFonts")
                    rpr.insert(0, f)
                for k in ("ascii", "hAnsi", "cs", "eastAsia"):
                    f.set(W + k, "Georgia")
            else:
                now = "FFFFFF" if was in ("", "AUTO", "1A1A1A", "127D80", "0B5456") else CHIP
            if c is None:
                c = etree.Element(W + "color")
                # colour sits after fonts, bold, italic... and before size in Word's order
                anchor = next((rpr.find(t, NS) for t in ("w:spacing", "w:w", "w:kern", "w:position", "w:sz",
                                                          "w:szCs", "w:highlight", "w:u", "w:effect",
                                                          "w:vertAlign", "w:lang") if rpr.find(t, NS) is not None), None)
                if anchor is not None:
                    anchor.addprevious(c)
                else:
                    rpr.append(c)
            c.set(W + "val", now)
    # a little air before what follows, the way the band stood before
    gap = etree.Element(W + "p")
    etree.SubElement(etree.SubElement(gap, W + "pPr"), W + "spacing", {W + "after": "0", W + "line": "120",
                                                                       W + "lineRule": "exact"})
    tbl.addnext(gap)
    return True


def mend_cells(body):
    """A table cell must end with a paragraph; one that does not makes Word
    offer to repair the file. The empty paragraph Word would add, added."""
    n = 0
    for tc in body.iter(W + "tc"):
        if len(tc) == 0 or tc[-1].tag != W + "p":
            tc.append(etree.Element(W + "p"))
            n += 1
    return n


def needs_mending(path):
    root = etree.fromstring(zipfile.ZipFile(path).read("word/document.xml"))
    return any(len(tc) == 0 or tc[-1].tag != W + "p" for tc in root.iter(W + "tc"))


def saved_pages(path):
    """The page count Word wrote into the file when it last saved it."""
    z = zipfile.ZipFile(path)
    m = re.search(r"<Pages>(\d+)</Pages>", z.read("docProps/app.xml").decode()) \
        if "docProps/app.xml" in z.namelist() else None
    return int(m.group(1)) if m else 0


EX_LABEL = re.compile(r"^\d+\.\d+$")


def keep_headings(body):
    """An exercise's instruction stays on the page with its first line: the
    new font is a little wider, and a heading must not be left at the foot of
    a page on its own."""
    n = 0
    for p in body.iter(W + "p"):
        runs = [r for r in p.findall("w:r", NS) if text_of(r)]
        if not runs or not EX_LABEL.match(text_of(runs[0])):
            continue
        c = runs[0].find("w:rPr/w:color", NS)
        if c is None or c.get(W + "val", "").upper() != "127D80":
            continue
        pr = ppr(p)
        if pr.find("w:keepNext", NS) is None:
            style = pr.find("w:pStyle", NS)
            k = etree.Element(W + "keepNext")
            if style is not None:
                style.addnext(k)
            else:
                pr.insert(0, k)
            n += 1
    return n


def recolour(xml):
    def swap(m):
        return m.group(1) + COLOURS.get(m.group(2).upper(), m.group(2)) + '"'
    xml = re.sub(r'((?:w:color w:val|w:fill|w:color)=")([0-9A-Fa-f]{6})"', swap, xml)

    def font(m):
        return m.group(1) + FONTS.get(m.group(2), m.group(2)) + '"'
    xml = re.sub(r'(w:(?:ascii|hAnsi|cs|eastAsia)=")([^"]+)"', font, xml)
    # text sizes only: a border's width is a w:sz attribute, and stays as it is
    xml = re.sub(r'(<w:sz(?:Cs)? w:val=")(\d+)"', lambda m: m.group(1) + str(max(1, round(int(m.group(2)) * SCALE))) + '"', xml)
    # a theme names its fonts too, and text with no font of its own takes them
    return re.sub(r'(<a:(?:latin|ea|cs) typeface=")(Calibri Light|Calibri|Cambria|Verdana)"',
                  lambda m: m.group(1) + ("Georgia" if m.group(2) == "Cambria" else "Aptos") + '"', xml)


def restyle(src, dst):
    """Write src's handout, in the site's clothes, to dst. Returns what changed."""
    zin = zipfile.ZipFile(src)
    os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
    report = {}
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            data = zin.read(info.filename)
            name = info.filename
            if name == "word/document.xml":
                root = etree.fromstring(data)
                body = root.find("w:body", NS)
                report["mended"] = mend_cells(body)
                report["boxes"] = dress_boxes(body)
                report["kept"] = keep_headings(body)
                report["cover"] = dress_cover(body)
                data = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
            if name.startswith("word/") and name.endswith(".xml"):     # the theme is word/theme/*.xml
                data = recolour(data.decode("utf-8")).encode("utf-8")
            zout.writestr(info, data)
    return report


def words(path):
    """Every piece of text in the file, part by part - to prove none changed."""
    import html as _html
    z = zipfile.ZipFile(path)
    return [(n, _html.unescape("".join(re.findall(r"<w:t(?: [^>]*)?>([^<]*)</w:t>", z.read(n).decode("utf-8")))))
            for n in sorted(z.namelist()) if n.startswith("word/") and n.endswith(".xml")]


# ---------------------------------------------------------------- every handout
HANDOUTS = os.path.expanduser("~/Desktop/Handouts")
OUT = os.path.expanduser("~/Desktop/Handouts (website style)")


def paper_handouts():
    """The paper handouts: not the answer keys, homework, ASRP packs, the
    website's "new design" copies or anything in a _work folder."""
    out = []
    for f in sorted(glob.glob(os.path.join(HANDOUTS, "**", "*.docx"), recursive=True)):
        rel = os.path.relpath(f, HANDOUTS)
        low = rel.lower()
        if (os.path.basename(f).startswith("~$") or "answer key" in low or "homework" in low
                or "new design" in low or "/asrp/" in low or "/_work/" in low):
            continue
        out.append(rel)
    return out


def word_pdf(docx, pdf):
    if os.path.exists(pdf):
        os.remove(pdf)                  # Word asks before replacing a file, and a script cannot answer
    _word_pdf(docx, pdf)


def _word_pdf(docx, pdf):
    """Word prints the file to PDF. Only the document it opened here is
    closed - whatever else is open in Word is left alone: it is the one that
    was not there before (some files open untitled, so not found by name).
    Word may only write where it is allowed to - the Desktop, not a temporary folder."""
    name = os.path.basename(docx).replace('"', '\\"')
    script = """
    with timeout of 300 seconds
      tell application "Microsoft Word"
        set k to count of documents
        open POSIX file "%s"
        if (count of documents) is not (k + 1) then error "it was open already"
        set d to document 1
        save as d file name "%s" file format format PDF
        close d saving no
      end tell
    end timeout""" % (docx, pdf)
    done = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=400)
    if done.returncode:
        raise SystemExit("Word could not print %s: %s" % (name, done.stderr.strip()))


def word_pages(docx):
    """How many pages Word makes of a file, without saving anything."""
    name = os.path.basename(docx).replace('"', '\\"')
    script = """
    with timeout of 300 seconds
      tell application "Microsoft Word"
        set k to count of documents
        open POSIX file "%s"
        if (count of documents) is not (k + 1) then error "it was open already"
        set d to document 1
        set n to compute statistics d statistic statistic pages
        close d saving no
        return n
      end tell
    end timeout""" % (docx,)
    done = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=400)
    if done.returncode:
        raise SystemExit("Word could not open %s: %s" % (name, done.stderr.strip()))
    return int(done.stdout.strip())


def pdf_pages(pdf):
    data = open(pdf, "rb").read()
    counts = [int(n) for n in re.findall(rb"/Type\s*/Pages\b[^>]*?/Count\s+(\d+)", data)]
    return max(counts) if counts else len(re.findall(rb"/Type\s*/Page\b", data))


def main():
    if sys.argv[1:2] != ["--all"]:
        src, dst = sys.argv[1], sys.argv[2]
        print(restyle(src, dst))
        return
    pdf = "--pdf" in sys.argv
    start = sys.argv[sys.argv.index("--from") + 1] if "--from" in sys.argv else None
    for rel in paper_handouts():
        if start:
            if start not in rel:
                continue
            start = None
        src, dst = os.path.join(HANDOUTS, rel), os.path.join(OUT, rel)
        rep = restyle(src, dst)
        same = words(src) == words(dst)
        line = "%-72s boxes %2d  cover %s  text %s" % (rel[:72], rep["boxes"], "yes" if rep["cover"] else "no ",
                                                      "same" if same else "CHANGED")
        if pdf:
            # an original Word would offer to repair is not opened: that offer waits for a click
            before = saved_pages(src) if needs_mending(src) else word_pages(src)
            word_pdf(dst, dst[:-5] + ".pdf")
            after = pdf_pages(dst[:-5] + ".pdf")
            line += "  pages %d -> %d%s" % (before, after, "" if before == after else "  MOVED")
        print(line, flush=True)


if __name__ == "__main__":
    main()
