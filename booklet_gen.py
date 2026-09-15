"""Build a booklet from scratch, in the same style the .docx ones are drawn in.

`booklet_html.py` renders a handout that already exists in Word. This writes
one that does not: same teal rules, same pale panels, same numbered sections,
and the blanks already marked up so the site can mark them.

A page is a list of blocks. Every {} in an exercise line becomes a box; give
it an answer and it is marked, give it None and it is the student's own words,
kept and shown back but never scored.

Designed narrow on purpose. Most of these students read on a phone, so the
content is a single column - no side-by-side exercise tables, which on a
390px screen become two columns wrapping every three words.
"""
import html, json, re

TEAL, DEEP, SOFT, GREY, INK, RULE = ("#127D80", "#0B5456", "#F2F8F8",
                                     "#6E6E6E", "#1A1A1A", "#C9C9C9")
BLANK = "{}"
Q = []                                   # every blank, in reading order


def esc(t):
    return html.escape(t)


def gaps(text, answers, label, num):
    """Turn {} into boxes, and remember the answer each one wants."""
    parts = text.split(BLANK)
    out = parts[0]
    for i, tail in enumerate(parts[1:]):
        ans = answers[i] if i < len(answers) else None
        Q.append({"num": len(Q) + 1,
                  "kind": "typed" if ans else "open",
                  "prompt": "%s  %s" % (label, re.sub(r"\s+", " ", text)[:150]),
                  "answer": ans, "options": []})
        out += ('<input class="bk-blank" data-q="%d" style="width:%dpx" '
                'autocomplete="off" autocapitalize="off" spellcheck="false">'
                % (len(Q), 150 if ans and len(ans) > 9 else 110))
        out += tail
    return out


def eyebrow(t):
    return (f'<p style="margin-bottom:2px"><span style="font-weight:700;'
            f'color:{TEAL};font-size:8pt;letter-spacing:1.6px">{esc(t)}</span></p>')


def title(t):
    return (f'<p style="margin-bottom:4px"><span style="font-weight:700;'
            f'color:{DEEP};font-size:20pt">{esc(t)}</span></p>')


def strap(bold, rest):
    return (f'<p style="margin-bottom:6px;border-bottom:1px solid {TEAL};'
            f'padding-bottom:6px"><span style="font-weight:700;font-size:10pt">'
            f'{esc(bold)}</span> <span style="font-style:italic;color:{GREY};'
            f'font-size:10pt">{esc(rest)}</span></p>')


def sheetbar(n, name, skill):
    return (f'<table class="bk"><tr>'
            f'<td style="background:{TEAL};width:120px;vertical-align:middle;'
            f'border:0"><p style="text-align:center;margin:0"><span '
            f'style="font-weight:700;color:#fff;font-size:12pt">SHEET {n}</span>'
            f'</p></td><td style="vertical-align:middle;border:0;'
            f'border-bottom:1px solid {TEAL}"><p style="margin:0">'
            f'<span style="font-weight:700;color:{DEEP};font-size:12pt">'
            f'{esc(name)}</span> <span style="color:{GREY};font-size:10pt">'
            f'&nbsp;·&nbsp; {esc(skill)}</span></p></td></tr></table>')


def part(letter, instruction):
    return (f'<p style="margin-top:14px;margin-bottom:4px">'
            f'<span style="font-weight:700;color:{TEAL};font-size:11pt">'
            f'{letter}</span> <span style="font-weight:700;font-size:11pt">'
            f'{esc(instruction)}</span></p>')


def p(text, style=""):
    return f'<p style="{style}">{text}</p>'


def plain(text):
    return p(f'<span style="font-size:10.5pt">{esc(text)}</span>')


def note(head, lines, colour=TEAL, fill=SOFT):
    inner = "".join(
        f'<p style="margin-bottom:3px"><span style="font-size:10pt">{l}</span></p>'
        for l in lines)
    return (f'<table class="bk"><tr><td style="background:{fill};'
            f'border:1px solid {colour};padding:10px 12px">'
            f'<table class="bk"><tr><td style="background:{colour};border:0;'
            f'width:130px"><p style="margin:0"><span style="font-weight:700;'
            f'color:#fff;font-size:8pt;letter-spacing:1.2px">{esc(head)}</span>'
            f'</p></td></tr></table>{inner}</td></tr></table>')


def numbered(label, items):
    """items: list of (sentence with {}, [answers])"""
    rows = ""
    for i, (text, answers) in enumerate(items, 1):
        rows += (f'<p style="margin-bottom:5px;padding-left:18px">'
                 f'<span style="color:{GREY};font-size:10pt">{i}</span> '
                 f'<span style="font-size:10.5pt">'
                 f'{gaps(text, answers, label, i)}</span></p>')
    return rows




def section(n, name, sub=""):
    """The numbered teal bar that opens a section of the booklet."""
    tail = (f' <span style="color:{GREY};font-size:10pt">&nbsp;·&nbsp; '
            f'{esc(sub)}</span>' if sub else "")
    return (f'<table class="bk"><tr>'
            f'<td style="background:{TEAL};width:110px;vertical-align:middle;'
            f'border:0"><p style="text-align:center;margin:0"><span '
            f'style="font-weight:700;color:#fff;font-size:13pt">{n}</span>'
            f'</p></td><td style="vertical-align:middle;border:0;'
            f'border-bottom:1px solid {TEAL}"><p style="margin:0">'
            f'<span style="font-weight:700;color:{DEEP};font-size:12pt">'
            f'{esc(name)}</span>{tail}</p></td></tr></table>')


def exercise(label, instruction):
    return (f'<p style="margin-top:14px;margin-bottom:4px">'
            f'<span style="font-weight:700;color:{TEAL};font-size:11pt">'
            f'{esc(label)}</span> <span style="font-weight:700;font-size:11pt">'
            f'{esc(instruction)}</span></p>')


def text_block(head, paragraphs):
    """A reading passage: a titled panel, one column, phone-shaped."""
    inner = "".join(
        f'<p style="margin-bottom:6px"><span style="font-size:10.5pt">{t}</span>'
        f'</p>' for t in paragraphs)
    return (f'<table class="bk"><tr><td style="background:#fff;'
            f'border:1px solid {TEAL};padding:12px 14px">'
            f'<p style="margin-bottom:6px"><span style="font-weight:700;'
            f'color:{DEEP};font-size:12pt">{esc(head)}</span></p>{inner}'
            f'</td></tr></table>')


def header(unit, level, title_text, strapline, contents, learn, prepared_by):
    h = [eyebrow(f"{unit}        {level}"), title(title_text)]
    bold, _, rest = strapline.partition(" · ")
    h.append(strap(bold, rest))
    h.append(note("IN THIS BOOKLET", contents))
    h.append(note("YOU WILL LEARN TO", learn))
    h.append(p(f'<span style="font-weight:700;color:{GREY};font-size:9pt;'
               f'letter-spacing:1.4px">NAME</span> '
               f'<span style="color:{RULE}">………………………………</span> '
               f'<span style="font-weight:700;color:{GREY};font-size:9pt;'
               f'letter-spacing:1.4px">CLASS</span> '
               f'<span style="color:{RULE}">…………………</span> '
               f'<span style="font-weight:700;color:{GREY};font-size:9pt;'
               f'letter-spacing:1.4px">DATE</span> '
               f'<span style="color:{RULE}">…………………</span>'
               f'&nbsp;&nbsp;<span style="font-size:9pt;color:{GREY}">'
               f'Prepared by </span><span style="font-weight:700;color:{DEEP};'
               f'font-size:9pt">{esc(prepared_by)}</span>',
               f"border-top:1px solid {RULE};padding-top:6px;margin-bottom:10px"))
    return h


def finish(blocks, level, number, title_text):
    layout = '<div class="booklet">%s</div>' % "".join(blocks)
    marked = sum(1 for q in Q if q["kind"] == "typed")
    return ({"level": level, "number": number, "title": title_text,
             "passages": {}, "layout": layout, "questions": list(Q)},
            len(Q), marked)
