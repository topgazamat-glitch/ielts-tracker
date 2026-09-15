"""Turn a generated booklet into the two files a teacher actually hands out.

    python3 export_booklet.py e11bd.json --out ~/Desktop

Writes a PDF to print and a .docx to edit. The blanks come back as dotted
lines, because on paper that is what they are.

The PDF is printed by Chrome rather than by pdfmake.py: pdfmake writes text in
one font with no fills or table borders, which is right for a transcript and
would throw away everything that makes the handout look like the handout.

The .docx is written here, by hand. Word's format is a zip of XML, and the
subset this needs - paragraphs, runs with bold, italic, colour and size, and
tables with shaded cells - is small enough to write directly. That keeps the
project's one rule: standard library only.
"""
import argparse
import base64
import html.parser
import json
import os
import re
import sys
import time
import urllib.request
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import booklet_html as bh

DOTS = "…" * 12


def paper_html(layout, title):
    """The same booklet with writing lines instead of boxes."""
    body = re.sub(r'<input class="bk-blank"[^>]*>',
                  '<span class="wline">%s</span>' % DOTS, layout)
    return ("<!doctype html><meta charset='utf-8'><title>%s</title><style>"
            "@page { size: A4; margin: 16mm 14mm; }"
            "body { margin: 0; }"
            ".booklet .wline { color: #C9C9C9; letter-spacing: 1px; }"
            ".booklet table.bk { page-break-inside: avoid; }"
            ".booklet p { orphans: 2; widows: 2; }"
            % html.escape(title) + bh.PAGE_CSS +
            "</style><div class='booklet-page'>%s</div>" % body)


# ------------------------------------------------------------------- the pdf

def to_pdf(page_html, out):
    """Let Chrome print it, so the fills, rules and boxes survive."""
    import look                       # the headless Chrome already in the repo
    tmp = out + ".html"
    open(tmp, "w").write(page_html)
    look.start_chrome()
    tab = look.Tab("about:blank")
    tab.call("Page.enable")
    tab.call("Page.navigate", url="file://" + os.path.abspath(tmp))
    time.sleep(2.0)
    data = tab.call("Page.printToPDF", printBackground=True,
                    preferCSSPageSize=True, marginTop=0.6, marginBottom=0.6,
                    marginLeft=0.55, marginRight=0.55)["data"]
    tab.close()
    open(out, "wb").write(base64.b64decode(data))
    os.remove(tmp)
    return out


# ------------------------------------------------------------------ the docx

DOCX_RELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
             '<Relationships xmlns="http://schemas.openxmlformats.org/package/'
             '2006/relationships"><Relationship Id="rId1" Type="http://schemas'
             '.openxmlformats.org/officeDocument/2006/relationships/officeDocum'
             'ent" Target="word/document.xml"/></Relationships>')

CONTENT_TYPES = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                 '<Types xmlns="http://schemas.openxmlformats.org/package/2006/'
                 'content-types"><Default Extension="xml" ContentType="applicat'
                 'ion/xml"/><Default Extension="rels" ContentType="application/'
                 'vnd.openxmlformats-package.relationships+xml"/><Override Part'
                 'Name="/word/document.xml" ContentType="application/vnd.openxm'
                 'lformats-officedocument.wordprocessingml.document.main+xml"/>'
                 '</Types>')

W_NS = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"')


def xesc(t):
    return (t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def css_of(style):
    out = {}
    for bit in (style or "").split(";"):
        if ":" in bit:
            k, _, v = bit.partition(":")
            out[k.strip()] = v.strip()
    return out


def run_xml(text, css):
    """One <w:r>, carrying whatever of the style Word understands."""
    pr = []
    if css.get("font-weight") in ("700", "bold", "640", "650"):
        pr.append("<w:b/>")
    if css.get("font-style") == "italic":
        pr.append("<w:i/>")
    col = css.get("color", "")
    m = re.match(r"#([0-9A-Fa-f]{6})", col)
    if m:
        pr.append('<w:color w:val="%s"/>' % m.group(1).upper())
    size = css.get("font-size", "")
    m = re.match(r"([0-9.]+)pt", size)
    if m:
        half = int(round(float(m.group(1)) * 2))
        pr.append('<w:sz w:val="%d"/><w:szCs w:val="%d"/>' % (half, half))
    sp = css.get("letter-spacing", "")
    m = re.match(r"([0-9.]+)px", sp)
    if m:
        pr.append('<w:spacing w:val="%d"/>' % int(float(m.group(1)) * 20))
    rpr = "<w:rPr>%s</w:rPr>" % "".join(pr) if pr else ""
    return ('<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r>'
            % (rpr, xesc(text)))


class ToDocx(html.parser.HTMLParser):
    """The generated HTML is a subset we wrote ourselves, so it can be walked
    straight into WordprocessingML: paragraphs, styled runs, and one level of
    table with shaded cells."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.styles = []          # the style stack, innermost last
        self.runs = []            # runs of the paragraph being built
        self.ppr = ""
        self.in_p = False
        self.cells = None         # collecting a cell's body
        self.rows = None
        self.row = None
        self.depth = 0

    # -- helpers
    def emit(self, xml):
        (self.cells if self.cells is not None else self.out).append(xml)

    def css(self):
        merged = {}
        for s in self.styles:
            merged.update(s)
        return merged

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "span":
            self.styles.append(css_of(a.get("style")))
        elif tag == "p":
            self.in_p, self.runs = True, []
            c = css_of(a.get("style"))
            pr = []
            if c.get("text-align") == "center":
                pr.append('<w:jc w:val="center"/>')
            fill = re.match(r"#([0-9A-Fa-f]{6})", c.get("background", ""))
            if fill:
                pr.append('<w:shd w:val="clear" w:fill="%s"/>'
                          % fill.group(1).upper())
            self.ppr = "<w:pPr>%s</w:pPr>" % "".join(pr) if pr else ""
            self.styles.append(c)
        elif tag == "input":
            self.runs.append(run_xml(DOTS, {"color": "#C9C9C9"}))
        elif tag == "br":
            self.runs.append("<w:r><w:br/></w:r>")
        elif tag == "table":
            self.depth += 1
            if self.depth == 1:
                self.rows = []
        elif tag == "tr" and self.depth == 1:
            self.row = []
        elif tag == "td" and self.depth == 1:
            self.cells = []
            self.cell_css = css_of(a.get("style"))

    def handle_endtag(self, tag):
        if tag == "span" and self.styles:
            self.styles.pop()
        elif tag == "p":
            if self.styles:
                self.styles.pop()
            self.emit("<w:p>%s%s</w:p>" % (self.ppr, "".join(self.runs)))
            self.in_p, self.runs, self.ppr = False, [], ""
        elif tag == "td" and self.depth == 1:
            fill = re.match(r"#([0-9A-Fa-f]{6})",
                            self.cell_css.get("background", ""))
            shd = ('<w:shd w:val="clear" w:fill="%s"/>' % fill.group(1).upper()
                   if fill else "")
            body = "".join(self.cells) or "<w:p/>"
            self.row.append('<w:tc><w:tcPr><w:tcW w:w="0" w:type="auto"/>%s'
                            '</w:tcPr>%s</w:tc>' % (shd, body))
            self.cells = None
        elif tag == "tr" and self.depth == 1:
            self.rows.append("<w:tr>%s</w:tr>" % "".join(self.row))
            self.row = None
        elif tag == "table":
            if self.depth == 1 and self.rows is not None:
                grid = ('<w:tblGrid>%s</w:tblGrid>'
                        % ('<w:gridCol w:w="4675"/>'
                           * max(1, self.rows and self.rows[0].count("<w:tc>"))))
                self.out.append(
                    '<w:tbl><w:tblPr><w:tblW w:w="5000" w:type="pct"/>'
                    '<w:tblBorders>%s</w:tblBorders></w:tblPr>%s%s</w:tbl>'
                    % ("".join('<w:%s w:val="single" w:sz="4" w:color="D9D9D9"/>'
                               % s for s in ("top", "left", "bottom", "right",
                                             "insideH", "insideV")),
                       grid, "".join(self.rows)))
                self.rows = None
            self.depth = max(0, self.depth - 1)

    def handle_data(self, text):
        if not text.strip() and not self.in_p:
            return
        if self.in_p or self.cells is not None:
            self.runs.append(run_xml(text, self.css()))


def to_docx(layout, out, title):
    parser = ToDocx()
    parser.feed(layout)
    parser.close()
    body = "".join(parser.out)
    doc = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
           '<w:document %s><w:body>%s'
           '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
           '<w:pgMar w:top="900" w:right="800" w:bottom="900" w:left="800"/>'
           '</w:sectPr></w:body></w:document>' % (W_NS, body))
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", DOCX_RELS)
        z.writestr("word/document.xml", doc)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("handout", help="the json a handouts/ script writes")
    ap.add_argument("--out", default=".")
    args = ap.parse_args()
    data = json.load(open(args.handout))
    title = data.get("title", "Booklet").replace(" (booklet)", "")
    folder = os.path.expanduser(args.out)
    os.makedirs(folder, exist_ok=True)
    page = paper_html(data["layout"], title)
    pdf = to_pdf(page, os.path.join(folder, title + ".pdf"))
    doc = to_docx(data["layout"], os.path.join(folder, title + ".docx"), title)
    print(pdf, "%.0f KB" % (os.path.getsize(pdf) / 1024))
    print(doc, "%.0f KB" % (os.path.getsize(doc) / 1024))


if __name__ == "__main__":
    main()
