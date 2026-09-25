"""Write a paper handout as a Word file, in Azamat's own design.

The design is his. He took the booklets that were generated for him, changed
them by hand, and B02C is the result. This module reproduces that file's
typography exactly - A4, 850/1000 twip margins, Calibri 10.5 as the document
default with the body set at 11.5, Cambria only for the big title, and the
four colours (teal 127D80, deep teal 0B5456, grey 6E6E6E, panel F2F8F8).

Four things he asked to be fixed, and where each one lives:

  1. A task must not be broken across two pages. His files carry no
     keepNext, keepLines or cantSplit anywhere, which is exactly why a task
     of six questions put four on one page and two on the next. Every
     exercise here is emitted as one keep-together group, and every panel
     and table carries cantSplit.

  2. No Name / Class / Date block. There is none in the cover.

  3. The space for writing is sized from the number of words asked for, not
     guessed: `writing_lines()` gives roughly one ruled line per eight words,
     with a floor of three.

  4. Listening refers to a real Empower track and nothing else. `listening()`
     takes the track number from the coursebook and prints the sentence he
     wrote himself, so no handout ever asks for audio that does not exist.

A booklet is a list of blocks. Blocks are strings of WordprocessingML, built
by the helpers below, and `write()` packs them into a .docx using a template
file for the parts that never change.
"""
import html
import os
import re
import shutil
import zipfile

TEAL, DEEP, GREY, INK = "127D80", "0B5456", "6E6E6E", "1A1A1A"
PANEL, PANEL2, WARM, WARM_LINE = "F2F8F8", "E8F1F1", "FBF0EE", "C0745F"
WIDTH = 9360                    # table width in twips, as in his file
BODY = 23                       # half-points: 11.5pt
SMALL = 19

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "template.docx")


def E(t):
    return html.escape(str(t), quote=False).replace('"', "&quot;")


def run(text, size=BODY, colour=None, bold=False, italic=False, space=None,
        font=None):
    rpr = ""
    if bold:
        rpr += "<w:b/><w:bCs/>"
    if italic:
        rpr += "<w:i/><w:iCs/>"
    if font:
        rpr += ('<w:rFonts w:ascii="%s" w:eastAsia="%s" w:hAnsi="%s" '
                'w:cs="%s"/>' % (font, font, font, font))
    if colour:
        rpr += '<w:color w:val="%s"/>' % colour
    if space:
        rpr += '<w:spacing w:val="%d"/>' % space
    rpr += '<w:sz w:val="%d"/><w:szCs w:val="%d"/>' % (size, size)
    pres = ' xml:space="preserve"' if text != text.strip() else ""
    return "<w:r><w:rPr>%s</w:rPr><w:t%s>%s</w:t></w:r>" % (rpr, pres, E(text))


def para(runs, spacing="", ind="", keep=False, border="", tabs="",
         align=""):
    ppr = ""
    if keep:
        ppr += "<w:keepNext/><w:keepLines/>"
    if border:
        ppr += border
    if tabs:
        ppr += tabs
    if align:
        ppr += '<w:jc w:val="%s"/>' % align
    if spacing:
        ppr += "<w:spacing %s/>" % spacing
    if ind:
        ppr += "<w:ind %s/>" % ind
    inner = runs if isinstance(runs, str) else "".join(runs)
    return "<w:p><w:pPr>%s</w:pPr>%s</w:p>" % (ppr, inner)


def text(t, size=BODY, colour=None, bold=False, italic=False, keep=False,
         spacing='w:after="70" w:line="300" w:lineRule="auto"'):
    return para(run(t, size, colour, bold, italic), spacing=spacing, keep=keep)


def page_break():
    return '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'


# ----------------------------------------------------------------- tables

def _cell(content, width, fill=None, borders=None, pad=None):
    b = borders or {}
    edges = "".join(
        '<w:%s w:val="%s" w:sz="%d" w:space="0" w:color="%s"/>'
        % (side, b.get(side, ("none", 0, "FFFFFF"))[0],
           b.get(side, ("none", 0, "FFFFFF"))[1],
           b.get(side, ("none", 0, "FFFFFF"))[2])
        for side in ("top", "left", "bottom", "right"))
    shade = ('<w:shd w:val="clear" w:color="auto" w:fill="%s"/>' % fill
             if fill else "")
    margins = ('<w:tcMar><w:top w:w="%d" w:type="dxa"/>'
               '<w:left w:w="%d" w:type="dxa"/>'
               '<w:bottom w:w="%d" w:type="dxa"/>'
               '<w:right w:w="%d" w:type="dxa"/></w:tcMar>' % pad) if pad else ""
    return ('<w:tc><w:tcPr><w:tcW w:w="%d" w:type="dxa"/><w:tcBorders>%s'
            '</w:tcBorders>%s%s</w:tcPr>%s</w:tc>'
            % (width, edges, shade, margins, content))


def _table(grid, rows):
    cols = "".join('<w:gridCol w:w="%d"/>' % w for w in grid)
    return ('<w:tbl><w:tblPr><w:tblW w:w="%d" w:type="dxa"/>'
            '<w:tblCellMar><w:left w:w="10" w:type="dxa"/>'
            '<w:right w:w="10" w:type="dxa"/></w:tblCellMar>'
            '<w:tblLook w:val="0000"/></w:tblPr><w:tblGrid>%s</w:tblGrid>%s'
            '</w:tbl>' % (sum(grid), cols, "".join(rows)))


def _row(cells, keep=True):
    # cantSplit is the whole point: a panel or a question table is never
    # allowed to break over a page boundary
    props = "<w:trPr>%s</w:trPr>" % ("<w:cantSplit/>" if keep else "")
    return "<w:tr>%s%s</w:tr>" % (props, "".join(cells))


# ------------------------------------------------------------ the blocks

def cover(unit_line, level, title, lesson, strap, contents, learn,
          prepared_by="Olimov Azamat"):
    """Page one. No name, no class, no date - he cut those and was right."""
    out = [para([run(unit_line, 16, TEAL, bold=True, space=60),
                 "<w:r><w:tab/></w:r>",
                 run(level, 16, GREY, bold=True, space=60)],
                spacing='w:after="60"',
                tabs='<w:tabs><w:tab w:val="right" w:pos="9360"/></w:tabs>'),
           para(run(title, 40, DEEP, font="Cambria"),
                spacing='w:after="40" w:line="400" w:lineRule="auto"'),
           para([run(lesson, SMALL, bold=True),
                 run("      " + strap, SMALL, GREY, italic=True)],
                spacing='w:after="90"',
                border='<w:pBdr><w:bottom w:val="single" w:sz="6" '
                       'w:space="0" w:color="%s"/></w:pBdr>' % TEAL)]

    rows = [_row([_cell(para(run("In this booklet", SMALL, DEEP, bold=True),
                             spacing='w:after="60"'), WIDTH, fill=PANEL,
                        pad=(120, 160, 60, 160))])]
    items = ""
    for n, (name, page) in enumerate(contents, 1):
        items += para([run("%d    " % n, SMALL, TEAL, bold=True),
                       run(name, SMALL),
                       "<w:r><w:tab/></w:r>",
                       run(str(page), SMALL, GREY)],
                      spacing='w:after="30"',
                      tabs='<w:tabs><w:tab w:val="right" w:pos="8900"/>'
                           '</w:tabs>')
    rows.append(_row([_cell(items, WIDTH, fill=PANEL,
                            pad=(0, 160, 120, 160))]))
    out.append(_table([WIDTH], rows))

    out.append(text("You will learn to", SMALL, DEEP, bold=True, keep=True,
                    spacing='w:before="160" w:after="60"'))
    for line in learn:
        out.append(para([run("—  ", SMALL, TEAL), run(line, SMALL)],
                        spacing='w:after="30"',
                        ind='w:left="280" w:hanging="280"'))
    out.append(para(["<w:r><w:tab/></w:r>",
                     run("Prepared by  ", 16, GREY),
                     run(prepared_by, 17, DEEP, bold=True)],
                    spacing='w:before="140" w:after="200"',
                    tabs='<w:tabs><w:tab w:val="right" w:pos="9360"/></w:tabs>',
                    border='<w:pBdr><w:top w:val="single" w:sz="2" '
                           'w:space="0" w:color="D8D8D8"/></w:pBdr>'))
    # No page break: part one opens under the cover on page one, which is
    # how his own booklets run.
    return "".join(out)


def section(number, name):
    """The teal bar that opens a part."""
    num = para(run(str(number), 36, "FFFFFF", bold=True),
               spacing='w:before="40" w:after="40"', align="center")
    head = para(run(name, 26, DEEP, bold=True),
                spacing='w:before="90" w:after="90"')
    return _table([560, WIDTH - 560],
                  [_row([_cell(num, 560, fill=TEAL, pad=(60, 60, 60, 60)),
                         _cell(head, WIDTH - 560, pad=(60, 200, 60, 120))])])


def exercise(label, instruction):
    """The numbered instruction. Kept with whatever follows it."""
    return para([run(label + "  ", 24, TEAL, bold=True),
                 run(instruction, BODY, bold=True)],
                spacing='w:before="200" w:after="100"',
                ind='w:left="640" w:hanging="640"', keep=True)


def panel(heading, lines, fill=PANEL, edge=None, heading_colour=DEEP):
    """A box: key words, presentation, a reading text, a warning."""
    inner = ""
    if heading:
        inner += para(run(heading, SMALL, heading_colour, bold=True,
                          space=40),
                      spacing='w:after="70"')
    for line in lines:
        if isinstance(line, tuple):
            inner += para([run(line[0] + "  ", BODY, DEEP, bold=True),
                           run(line[1], BODY)],
                          spacing='w:after="40" w:line="300" '
                                  'w:lineRule="auto"')
        else:
            inner += para(run(line, BODY),
                          spacing='w:after="55" w:line="290" '
                                  'w:lineRule="auto"')
    borders = None
    if edge:
        borders = {s: ("single", 6, edge) for s in
                   ("top", "left", "bottom", "right")}
    return _table([WIDTH],
                  [_row([_cell(inner, WIDTH, fill=fill, borders=borders,
                               pad=(140, 200, 120, 200))])])


def reading(title_text, paragraphs):
    return panel(title_text, paragraphs, fill="FFFFFF",
                 edge="D8D8D8", heading_colour=DEEP)


def warning(heading, lines):
    return panel(heading, lines, fill=WARM, edge=WARM_LINE,
                 heading_colour=WARM_LINE)


def two_columns(items, dotted=14):
    """Questions side by side, which is what keeps a six-part task on one page.

    Left column gets the first half, right column the second, so 1-2-3 read
    down the left and 4-5-6 down the right, the way he set them out.
    """
    half = (len(items) + 1) // 2
    left, right = items[:half], items[half:]
    gap, col = 200, (WIDTH - 200) // 2
    rows = []
    for i in range(half):
        cells = []
        for side, start in ((left, 1), (right, half + 1)):
            k = i if side is left else i
            if k < len(side):
                n = start + k
                body = para([run("%d " % n, BODY, GREY),
                             run(side[k], BODY),
                             run("  " + "…" * dotted if dotted else "", BODY,
                                 GREY)],
                            spacing='w:after="60" w:line="300" '
                                    'w:lineRule="auto"',
                            ind='w:left="260" w:hanging="260"')
            else:
                body = para("")
            cells.append(body)
        rows.append(_row([_cell(cells[0], col, pad=(0, 0, 0, 100)),
                          _cell(para(""), gap),
                          _cell(cells[1], col, pad=(0, 100, 0, 0))]))
    return _table([col, gap, col], rows)


def questions(items, dotted=14):
    """One under another, for questions too long to sit in a column.

    Wrapped in a single borderless cell that cannot split. That is what
    stops four questions of a six-question task sitting on one page and the
    other two on the next - the complaint that started all of this. Word
    will not break the row, so it moves the whole task down instead.
    """
    out = []
    for n, q in enumerate(items, 1):
        out.append(para([run("%d " % n, BODY, GREY), run(q, BODY),
                         run("  " + "…" * dotted if dotted else "", BODY,
                             GREY)],
                        spacing='w:after="60" w:line="300" '
                                'w:lineRule="auto"',
                        ind='w:left="260" w:hanging="260"'))
    return _table([WIDTH], [_row([_cell("".join(out), WIDTH)])])


def writing_lines(words, per_line=8, minimum=3):
    """Ruled lines sized to the task.

    He pointed out that a task asking for a hundred words was given three
    lines. About eight words fit on a ruled line at this measure, so a
    hundred words needs twelve or thirteen, not three.
    """
    n = max(minimum, int(round(float(words) / per_line)))
    rule = ('<w:pBdr><w:bottom w:val="single" w:sz="4" w:space="1" '
            'w:color="C9C9C9"/></w:pBdr>')
    lines = "".join(
        para("", spacing='w:after="0" w:line="400" w:lineRule="auto"',
             border=rule) for _ in range(n))
    return _table([WIDTH], [_row([_cell(lines, WIDTH)])])


def listening(track, intro_lines):
    """The box before a listening task.

    Every handout uses the coursebook audio and nothing else, so the track
    number is the real one and the sentence is the one he wrote.
    """
    lines = list(intro_lines) + [
        "If your class has the audio, this is track %s. If not, your teacher "
        "will read the script — the tasks are the same." % track]
    return panel("BEFORE YOU LISTEN", lines, fill=PANEL2)


# ------------------------------------------------------------- the file

def _header_xml(unit_no, title, lesson):
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<w:hdr xmlns:w="http://schemas.openxmlformats.org/wordprocessing'
            'ml/2006/main">%s</w:hdr>'
            % para([run("%s  " % unit_no, 16, TEAL, bold=True),
                    run(title, 16, GREY),
                    "<w:r><w:tab/></w:r>",
                    run(lesson, 16, GREY)],
                   spacing='w:after="0"',
                   tabs='<w:tabs><w:tab w:val="right" w:pos="9360"/></w:tabs>',
                   border='<w:pBdr><w:bottom w:val="single" w:sz="2" '
                          'w:space="4" w:color="D8D8D8"/></w:pBdr>'))


def _footer_xml(level, prepared_by="Olimov Azamat"):
    page = ('<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
            '<w:r><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>'
            '<w:r><w:fldChar w:fldCharType="separate"/></w:r>'
            '<w:r><w:rPr><w:color w:val="%s"/><w:sz w:val="16"/></w:rPr>'
            '<w:t>1</w:t></w:r>'
            '<w:r><w:fldChar w:fldCharType="end"/></w:r>' % GREY)
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessing'
            'ml/2006/main">%s</w:ftr>'
            % para([run(prepared_by, 16, GREY),
                    "<w:r><w:tab/></w:r>",
                    run(level, 16, GREY),
                    "<w:r><w:tab/></w:r>", page],
                   spacing='w:before="60" w:after="0"',
                   tabs='<w:tabs><w:tab w:val="center" w:pos="4680"/>'
                        '<w:tab w:val="right" w:pos="9360"/></w:tabs>'))


SECT = ('<w:sectPr><w:headerReference w:type="default" r:id="rId8"/>'
        '<w:footerReference w:type="default" r:id="rId9"/>'
        '<w:pgSz w:w="11906" w:h="16838"/>'
        '<w:pgMar w:top="850" w:right="1000" w:bottom="850" w:left="1000"'
        ' w:header="708" w:footer="708" w:gutter="0"/>'
        '<w:cols w:space="720"/><w:docGrid w:linePitch="360"/></w:sectPr>')


def write(path, blocks, unit_no, title, lesson, level,
          template=TEMPLATE):
    """Pack the blocks into a .docx, borrowing the fixed parts from a template."""
    body = "".join(blocks) + SECT
    doc = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
           '<w:document xmlns:w="http://schemas.openxmlformats.org/'
           'wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats'
           '.org/officeDocument/2006/relationships"><w:body>%s</w:body>'
           '</w:document>' % body)
    made = {"word/document.xml": doc,
            "word/header1.xml": _header_xml(unit_no, title, lesson),
            "word/footer1.xml": _footer_xml(level)}
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with zipfile.ZipFile(template) as src, \
            zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as out:
        for item in src.infolist():
            if item.filename in made:
                out.writestr(item.filename, made[item.filename])
            else:
                out.writestr(item, src.read(item.filename))
    return path
