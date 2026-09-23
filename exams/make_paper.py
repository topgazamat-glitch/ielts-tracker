"""Lay the mock paper out as a page, then as a PDF and a Word file.

Plain and exam-like on purpose: no colour, no boxes competing with the
questions, numbers where the eye expects them. The same generator writes the
answer key and the audioscript, so the three can never drift apart.

    python3 exams/make_paper.py --out ~/Desktop/A2\\ Mock\\ Final
"""
import argparse
import html
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
import a2_mock_final as paper   # replaced by --paper; see main()

E = html.escape
LETTERS = "ABC"

CSS = """
.exam { font-family: Georgia, 'Times New Roman', serif; color:#111;
        line-height:1.45; font-size:11.5pt; }
.exam h1 { font-size:19pt; margin:0 0 2px; letter-spacing:-.01em; }
.exam .sub { font-size:10pt; color:#444; margin:0 0 14px; }
.exam h2 { font-size:13pt; margin:22px 0 2px; border-top:2px solid #111;
           padding-top:8px; }
.exam h3 { font-size:11.5pt; margin:16px 0 4px; }
.exam .rubric { font-style:italic; color:#333; margin:0 0 10px; font-size:10.5pt; }
.exam .q { margin:0 0 7px; }
.exam .q b { display:inline-block; min-width:26px; }
.exam .opts { margin:0 0 9px 26px; }
.exam .opts span { display:inline-block; min-width:150px;
                   padding-right:22px; white-space:nowrap; }
.exam .opts { line-height:1.9; }
.exam table.box { border-collapse:collapse; width:100%; margin:8px 0 14px; }
.exam table.box td { border:1px solid #111; padding:7px 9px; vertical-align:top;
                     font-size:10.5pt; }
.exam .text p { margin:0 0 8px; text-align:justify; }
.exam .lines { border-bottom:1px solid #999; height:22px; margin:0 0 4px; }
.exam .note { font-size:10pt; color:#555; }
"""


def block(title, rubric, body):
    return ('<h2>%s</h2><p class="rubric">%s</p>%s'
            % (E(title), E(rubric), body))


def mcq(num, stem, options, inline=False):
    opts = "".join('<span>%s) %s</span>' % (LETTERS[i], E(o))
                   for i, o in enumerate(options))
    return ('<p class="q"><b>%s</b> %s</p><p class="opts">%s</p>'
            % (num, E(stem), opts))


def listening_html():
    out = ['<h2>LISTENING</h2><p class="rubric">Four parts, twenty questions. '
           'You will hear every part twice.</p>']

    out.append('<h3>PART 1 &nbsp; QUESTIONS 1-5</h3>')
    out.append('<p class="rubric">You will hear five short conversations. For '
               'each question, choose A, B or C.</p>')
    for item in paper.PART1:
        out.append(mcq(item["q"], item["ask"], item["options"]))

    out.append('<h3>PART 2 &nbsp; QUESTIONS 6-10</h3>')
    out.append('<p class="rubric">%s</p>' % E(paper.PART2["intro"]))
    left = "".join('<p class="q"><b>%s</b> %s &nbsp;……………</p>' % (n, E(who))
                   for n, who in paper.PART2["people"])
    right = "".join('<p class="q"><b>%s</b> %s</p>' % (L, E(t))
                    for L, t in paper.PART2["options"])
    out.append('<table class="box"><tr><td>%s</td><td>%s</td></tr></table>'
               % (left, right))

    out.append('<h3>PART 3 &nbsp; QUESTIONS 11-15</h3>')
    out.append('<p class="rubric">%s</p>' % E(paper.PART3["intro"]))
    for q in paper.PART3["questions"]:
        out.append(mcq(q["q"], q["stem"], q["options"]))

    out.append('<h3>PART 4 &nbsp; QUESTIONS 16-20</h3>')
    out.append('<p class="rubric">%s</p>' % E(paper.PART4["intro"]))
    rows = "".join(
        '<p class="q"><b>%s</b> %s &nbsp;……………………………</p>' % (g["q"], E(g["label"]))
        for g in paper.PART4["gaps"])
    out.append('<table class="box"><tr><td><p class="q"><b></b>%s</p>%s</td>'
               '</tr></table>' % (E(paper.PART4["title"]), rows))
    return "".join(out)


def reading_html():
    out = ['<h2>READING AND WRITING</h2><p class="rubric">Five parts, '
           'twenty-five questions, and one email to write.</p>']

    out.append('<h3>PART 1 &nbsp; QUESTIONS 1-5</h3>')
    out.append('<p class="rubric">%s</p>' % E(R1["intro"]))
    notices = "".join('<p class="q"><b>%s</b> %s</p>' % (L, E(t))
                      for L, t in R1["notices"])
    out.append('<table class="box"><tr><td>%s</td></tr></table>' % notices)
    for n, text, _a in R1["items"]:
        out.append('<p class="q"><b>%s</b> %s &nbsp;……………</p>' % (n, E(text)))

    out.append('<h3>PART 2 &nbsp; QUESTIONS 6-10</h3>')
    out.append('<p class="rubric">%s</p>' % E(R2["intro"]))
    for n, stem, opts, _a in R2["items"]:
        out.append(mcq(n, stem, opts))

    out.append('<h3>PART 3 &nbsp; QUESTIONS 11-15</h3>')
    out.append('<p class="rubric">%s</p>' % E(R3["intro"]))
    body = "".join("<p>%s</p>" % E(p) for p in R3["text"])
    out.append('<table class="box"><tr><td><p class="q"><b></b>%s</p>'
               '<div class="text">%s</div></td></tr></table>'
               % (E(R3["title"]), body))
    for q in R3["questions"]:
        out.append(mcq(q["q"], q["stem"], q["options"]))

    out.append('<h3>PART 4 &nbsp; QUESTIONS 16-20</h3>')
    out.append('<p class="rubric">%s</p>' % E(R4["intro"]))
    out.append('<table class="box"><tr><td><p class="q"><b></b>%s</p>'
               '<div class="text"><p>%s</p></div></td></tr></table>'
               % (E(R4["title"]), E(R4["text"])))
    for n, opts, _a in R4["items"]:
        out.append(mcq(n, "", opts))

    out.append('<h3>PART 5 &nbsp; QUESTIONS 21-25</h3>')
    out.append('<p class="rubric">%s</p>' % E(R5["intro"]))
    for greeting, body, sign in R5["letters"]:
        out.append('<table class="box"><tr><td><p>%s</p><div class="text">'
                   '<p>%s</p></div><p>%s</p></td></tr></table>'
                   % (E(greeting), E(body), E(sign).replace("\n", "<br>")))

    out.append('<h3>WRITING</h3>')
    out.append('<p class="rubric">%s</p>' % E(paper.WRITING["task"]))
    out.append("".join("<p class=\"q\">&bull; %s</p>" % E(p)
                       for p in paper.WRITING["points"]))
    out.append('<p class="rubric">%s</p>' % E(paper.WRITING["words"]))
    out.append('<div class="lines"></div>' * 9)
    return "".join(out)


R1, R2, R3, R4, R5 = (paper.R_PART1, paper.R_PART2, paper.R_PART3,
                      paper.R_PART4, paper.R_PART5)


def key_html():
    rows = []
    rows.append("<h2>ANSWER KEY</h2>")
    rows.append("<h3>Listening</h3>")
    pairs = [(i["q"], i["answer"]) for i in paper.PART1]
    pairs += [(int(n), paper.PART2["answers"][n]) for n, _w in paper.PART2["people"]]
    pairs += [(q["q"], q["answer"]) for q in paper.PART3["questions"]]
    pairs += [(g["q"], g["answer"]) for g in paper.PART4["gaps"]]
    rows.append('<p class="q">' + " &nbsp;&middot;&nbsp; ".join(
        "<b>%s</b> %s" % (n, E(str(a))) for n, a in pairs) + "</p>")

    rows.append("<h3>Reading and Writing</h3>")
    pairs = [(n, a) for n, _t, a in R1["items"]]
    pairs += [(n, a) for n, _s, _o, a in R2["items"]]
    pairs += [(q["q"], q["answer"]) for q in R3["questions"]]
    pairs += [(n, a) for n, _o, a in R4["items"]]
    pairs += sorted(R5["answers"].items())
    rows.append('<p class="q">' + " &nbsp;&middot;&nbsp; ".join(
        "<b>%s</b> %s" % (n, E(str(a))) for n, a in pairs) + "</p>")

    rows.append("<h3>Marks</h3>")
    rows.append('<p class="q">Listening 20 &nbsp;&middot;&nbsp; Reading and '
                'Writing 25 &nbsp;&middot;&nbsp; Email marked on the four '
                'points, not on length. A student who covers all four points '
                'in clear sentences has done what the task asks.</p>')
    rows.append('<p class="note">Where two answers are given for one gap, '
                'either is correct.</p>')
    return "".join(rows)


def script_html():
    out = ["<h2>AUDIOSCRIPT</h2>",
           '<p class="rubric">Read this aloud if you would rather not use the '
           'recording. Every part is heard twice.</p>']

    def turns(lines):
        return "".join('<p class="q"><b>%s</b> %s</p>'
                       % (E(v.split(" ")[0]), E(t)) for v, t in lines)

    out.append("<h3>Part 1</h3>")
    for item in paper.PART1:
        out.append('<p class="q"><b>Q%s</b> <i>%s</i></p>' % (item["q"], E(item["ask"])))
        out.append(turns(item["lines"]))
    out.append("<h3>Part 2</h3>" + turns(paper.PART2["lines"]))
    out.append("<h3>Part 3</h3>" + turns(paper.PART3["lines"]))
    out.append("<h3>Part 4</h3>" + turns(paper.PART4["lines"]))
    return "".join(out)


def page(title, inner):
    return ("<title>%s</title><style>@page{size:A4;margin:16mm 15mm}"
            "body{margin:0}%s</style>"
            '<div class="exam"><h1>%s</h1>'
            '<p class="sub">A2 Elementary &middot; mock final &middot; '
            'name ………………………………  class …………  date …………</p>%s</div>'
            % (E(title), CSS, E(title), inner))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paper", default="a2_mock_final",
                    help="the content module, e.g. a2_mock_2")
    ap.add_argument("--out", default=os.path.expanduser("~/Desktop/A2 Mock Final"))
    args = ap.parse_args()
    global paper
    paper = __import__(args.paper)
    out = os.path.expanduser(args.out)
    os.makedirs(out, exist_ok=True)
    import export_booklet as ex

    for name, inner in (
            ("A2 Mock Final - Question paper",
             listening_html() + reading_html()),
            ("A2 Mock Final - Answer key", key_html()),
            ("A2 Mock Final - Audioscript", script_html())):
        html_page = page(name, inner)
        ex.to_pdf(html_page, os.path.join(out, name + ".pdf"))
        ex.to_docx(inner, os.path.join(out, name + ".docx"), name)
        print("   %-42s written" % name)


if __name__ == "__main__":
    main()
