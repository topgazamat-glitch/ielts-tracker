"""Build a Competency mock final: paper, key, audioscript, digital test.

    python3 exams/make_competency.py b1plus --paper --out ~/Desktop/B1+\\ Mock
    python3 exams/make_competency.py b1 --digital --minutes 60 --strict --upload

The Empower Competency papers - B1 for Pre-Intermediate, B1+ for Intermediate
- share one skeleton: four listening parts for twenty marks, five reading
parts for twenty-five, and two writing tasks. What separates them is how many
options each reading question offers, three or four, and how hard the texts
are. So one builder makes both, and the number of options comes from the
paper itself rather than from a setting here.

The A2 paper has a different skeleton - one writing task, matching rather
than YES/NO - and keeps its own builder in make_paper.py and make_digital.py.
"""
import argparse
import html
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
from make_paper import CSS

PAPERS = {"b1": ("b1_mock_final", "B1 Pre-Intermediate", "B1 Mock Final"),
          "b1plus": ("b1plus_mock_final", "B1+ Intermediate", "B1+ Mock Final")}
# the extra Intermediate papers, which are Reading and Writing only
for _n in range(2, 7):
    PAPERS["b1plus-%d" % _n] = ("b1plus_mock_%d" % _n, "B1+ Intermediate",
                                "B1+ Mock %d" % _n)
paper = None      # set by main() from the chosen level
LEVEL_LINE = ""   # what the top of the printed paper says
DIGITAL_HEAD = ""

E = html.escape
LETTERS = "ABCD"
TEAL, DEEP, GREY = "#127D80", "#0B5456", "#6E6E6E"

# --------------------------------------------------------- the printed paper


def mcq(num, stem, options):
    opts = "".join('<span>%s) %s</span>' % (LETTERS[i], E(o))
                   for i, o in enumerate(options))
    return ('<p class="q"><b>%s</b> %s</p><p class="opts">%s</p>'
            % (num, E(stem), opts))


def yesno(num, text):
    return ('<p class="q"><b>%s</b> %s &nbsp;&nbsp; YES / NO</p>'
            % (num, E(text)))


def boxed(lines):
    return ('<table class="box"><tr><td>%s</td></tr></table>'
            % "".join("<p>%s</p>" % l for l in lines))


def listening_html():
    out = ['<h2>LISTENING</h2><p class="rubric">Four parts, twenty questions. '
           'Approximately 20 minutes. You will hear each part twice.</p>']

    out.append('<h3>PART 1 &nbsp; QUESTIONS 1-5</h3>')
    out.append('<p class="rubric">You will hear five short recordings. For '
               'each question, choose the correct answer A, B or C.</p>')
    for it in paper.PART1:
        opts = "".join('<span>%s) %s</span>' % ("ABC"[i], E(o))
                       for i, o in enumerate(it["options"]))
        out.append('<p class="q"><b>%s</b> %s</p><p class="opts">%s</p>'
                   % (it["q"], E(it["ask"]), opts))

    out.append('<h3>PART 2 &nbsp; QUESTIONS 6-10</h3>')
    out.append('<p class="rubric">%s</p>' % E(paper.PART2["intro"]))
    rows = "".join(
        '<p>%s: &nbsp; (%s) ………………………………………</p>' % (E(g["label"]), g["q"])
        for g in paper.PART2["gaps"])
    out.append(boxed(["<b>%s</b>" % E(paper.PART2["title"]), rows]))

    out.append('<h3>PART 3 &nbsp; QUESTIONS 11-15</h3>')
    out.append('<p class="rubric">%s</p>' % E(paper.PART3["intro"]))
    for q in paper.PART3["questions"]:
        opts = "".join('<span>%s) %s</span>' % ("ABC"[i], E(o))
                       for i, o in enumerate(q["options"]))
        out.append('<p class="q"><b>%s</b> %s</p><p class="opts">%s</p>'
                   % (q["q"], E(q["ask"]), opts))

    out.append('<h3>PART 4 &nbsp; QUESTIONS 16-20</h3>')
    out.append('<p class="rubric">%s</p>' % E(paper.PART4["intro"]))
    for s in paper.PART4["statements"]:
        out.append(yesno(s["q"], s["text"]))
    return "".join(out)


def reading_html():
    R1, R2, R3, R4, R5 = (paper.R_PART1, paper.R_PART2, paper.R_PART3,
                          paper.R_PART4, paper.R_PART5)
    out = ['<h2>READING</h2><p class="rubric">Five parts, twenty-five '
           'questions. 30 minutes.</p>']

    out.append('<h3>PART 1 &nbsp; QUESTIONS 1-5</h3>')
    out.append('<p class="rubric">%s</p>' % E(R1["intro"]))
    for q in R1["questions"]:
        out.append(boxed([E(q["text"])]))
        out.append(mcq(q["q"], q["ask"], q["options"]))

    out.append('<h3>PART 2 &nbsp; QUESTIONS 6-10</h3>')
    out.append('<p class="rubric">%s</p>' % E(R2["intro"]))
    out.append(boxed(["<b>%s</b>" % E(R2["title"])] + [E(p) for p in R2["text"]]))
    for s in R2["statements"]:
        out.append(yesno(s["q"], s["text"]))

    out.append('<h3>PART 3 &nbsp; QUESTIONS 11-15</h3>')
    out.append('<p class="rubric">%s</p>' % E(R3["intro"]))
    out.append(boxed(["<b>%s</b>" % E(R3["title"])] + [E(p) for p in R3["text"]]))
    for q in R3["questions"]:
        out.append(mcq(q["q"], q["ask"], q["options"]))

    out.append('<h3>PART 4 &nbsp; QUESTIONS 16-20</h3>')
    out.append('<p class="rubric">%s</p>' % E(R4["intro"]))
    out.append(boxed(["<b>%s</b>" % E(R4["title"]), E(R4["text"])]))
    for g in R4["gaps"]:
        out.append(mcq(g["q"], "", g["options"]))

    out.append('<h3>PART 5 &nbsp; QUESTIONS 21-25</h3>')
    out.append('<p class="rubric">%s</p>' % E(R5["intro"]))
    out.append(boxed(["<b>%s</b>" % E(R5["title"])] +
                     [E(p) for p in R5["text"].split("\n") if p.strip()]))
    for g in R5["gaps"]:
        out.append('<p class="q"><b>%s</b> ………………………………………</p>' % g["q"])
    return "".join(out)


def writing_html():
    out = ['<h2>WRITING</h2><p class="rubric">Two parts. 30 minutes. Write '
           'clearly in pen, not pencil.</p>']
    out.append('<h3>QUESTION 1</h3>')
    out.append('<p class="rubric">%s</p>' % E(paper.WRITING1["task"]))
    out.append("".join("<p>&bull; %s</p>" % E(p) for p in paper.WRITING1["points"]))
    out.append('<p class="rubric">%s</p>' % E(paper.WRITING1["words"]))
    out.append('<div class="lines"></div>' * 6)
    out.append('<h3>QUESTION 2</h3>')
    out.append('<p class="rubric">%s</p>' % E(paper.WRITING2["task"]))
    out.append(boxed([E(paper.WRITING2["quote"])]))
    out.append('<p class="rubric">%s</p>' % E(paper.WRITING2["words"]))
    out.append('<div class="lines"></div>' * 14)
    return "".join(out)


def key_html():
    def rows(pairs):
        return "".join('<p class="q"><b>%s</b> %s</p>' % (n, E(str(a)))
                       for n, a in pairs)
    out = ['<h2>ANSWER KEY</h2>']
    out.append('<h3>Listening</h3>')
    out.append(rows([(i["q"], i["answer"]) for i in paper.PART1] +
                    [(g["q"], g["answer"]) for g in paper.PART2["gaps"]] +
                    [(q["q"], q["answer"]) for q in paper.PART3["questions"]] +
                    [(s["q"], s["answer"]) for s in paper.PART4["statements"]]))
    out.append('<h3>Reading</h3>')
    out.append(rows([(q["q"], q["answer"]) for q in paper.R_PART1["questions"]] +
                    [(s["q"], s["answer"]) for s in paper.R_PART2["statements"]] +
                    [(q["q"], q["answer"]) for q in paper.R_PART3["questions"]] +
                    [(g["q"], g["answer"]) for g in paper.R_PART4["gaps"]] +
                    [(g["q"], g["answer"]) for g in paper.R_PART5["gaps"]]))
    out.append('<h3>Marks</h3><p class="note">Listening 20 &middot; Reading 25 '
               '&middot; Writing marked by the teacher. A slash in the key '
               'means either word is accepted.</p>')
    return "".join(out)


def script_html():
    def turns(lines):
        return "".join("<p><b>%s</b> %s</p>" % (v.split(" ")[0], E(t))
                       for v, t in lines)
    out = ['<h2>AUDIOSCRIPT</h2>']
    out.append("<h3>Part 1</h3>")
    for it in paper.PART1:
        out.append("<p><b>Question %s</b> %s</p>" % (it["q"], E(it["ask"])))
        out.append(turns(it["lines"]))
    out.append("<h3>Part 2</h3>" + turns(paper.PART2["lines"]))
    out.append("<h3>Part 3</h3>" + turns(paper.PART3["lines"]))
    out.append("<h3>Part 4</h3>" + turns(paper.PART4["lines"]))
    return "".join(out)


def page(title, inner):
    return ("<title>%s</title><style>@page{size:A4;margin:16mm 15mm}"
            "body{margin:0}%s</style>"
            '<div class="exam"><h1>%s</h1>'
            '<p class="sub">%s &middot; mock final &middot; '
            'name ………………………………  class …………  date …………</p>%s</div>'
            % (E(title), CSS, E(title), E(LEVEL_LINE), inner))


# ------------------------------------------------------------- the website

QS = []


def ask(kind, prompt, answer, options=None):
    QS.append({"num": len(QS) + 1, "kind": kind, "prompt": prompt[:180],
               "answer": answer,
               "options": [{"letter": L, "text": t}
                           for L, t in (options or [])]})
    n = len(QS)
    if kind == "mcq":
        return '<span data-mcq="%d"></span>' % n
    if kind == "open":
        return '<span data-long="%d"></span>' % n
    return ('<input class="bk-blank" data-q="%d" style="width:150px"'
            ' autocomplete="off" autocapitalize="off" spellcheck="false">' % n)


def head(text, size=12, colour=DEEP, space=6):
    return ('<p style="margin-bottom:%dpx"><span style="font-weight:700;'
            'color:%s;font-size:%dpt">%s</span></p>' % (space, colour, size, E(text)))


def rubric(text):
    return ('<p style="margin-bottom:8px"><span style="font-style:italic;'
            'color:%s;font-size:10pt">%s</span></p>' % (GREY, E(text)))


def part_bar(n, title):
    return ('<table class="bk"><tr>'
            '<td style="background:%s;width:92px;border:0;vertical-align:middle">'
            '<p style="text-align:center;margin:0"><span style="font-weight:700;'
            'color:#fff;font-size:11pt">PART %s</span></p></td>'
            '<td style="border:0;border-bottom:1px solid %s;vertical-align:middle">'
            '<p style="margin:0"><span style="font-weight:700;color:%s;'
            'font-size:11pt">%s</span></p></td></tr></table>'
            % (TEAL, n, TEAL, DEEP, E(title)))


def item(num, text, control=""):
    return ('<p style="margin-bottom:6px;padding-left:16px">'
            '<span style="color:%s;font-size:10pt">%s</span> '
            '<span style="font-size:10.5pt">%s</span> %s</p>'
            % (GREY, num, text, control))


def panel(lines, fill="#F2F8F8", edge=TEAL):
    inner = "".join('<p style="margin-bottom:4px"><span style="font-size:10.5pt">'
                    '%s</span></p>' % l for l in lines)
    return ('<table class="bk"><tr><td style="background:%s;border:1px solid %s;'
            'padding:10px 12px">%s</td></tr></table>' % (fill, edge, inner))


# the letter is the whole answer here, so there is no text to repeat
YN = [("YES", ""), ("NO", "")]


def digital_layout():
    R1, R2, R3 = paper.R_PART1, paper.R_PART2, paper.R_PART3
    R4, R5 = paper.R_PART4, paper.R_PART5
    h = [head(DIGITAL_HEAD, 9, TEAL, 2),
         head("Reading and Writing", 20),
         rubric("Five reading parts, twenty-five questions, and two pieces of "
                "writing. Answer every question — a wrong answer costs "
                "nothing.")]

    h.append(part_bar(1, "Questions 1–5 · short texts"))
    h.append(rubric(R1["intro"]))
    for q in R1["questions"]:
        h.append(panel([E(q["text"])], fill="#fff"))
        h.append(item(q["q"], E(q["ask"]),
                      ask("mcq", "%d %s" % (q["q"], q["ask"]), q["answer"],
                          list(zip(LETTERS, q["options"])))))

    h.append(part_bar(2, "Questions 6–10 · the review"))
    h.append(rubric(R2["intro"]))
    h.append(panel([("<b>%s</b>" % E(R2["title"]))] +
                   [E(p) for p in R2["text"]], fill="#fff"))
    for s in R2["statements"]:
        h.append(item(s["q"], E(s["text"]),
                      ask("mcq", "%d %s" % (s["q"], s["text"]), s["answer"], YN)))

    h.append(part_bar(3, "Questions 11–15 · the article"))
    h.append(rubric(R3["intro"]))
    h.append(panel([("<b>%s</b>" % E(R3["title"]))] +
                   [E(p) for p in R3["text"]], fill="#fff"))
    for q in R3["questions"]:
        h.append(item(q["q"], E(q["ask"]),
                      ask("mcq", "%d %s" % (q["q"], q["ask"]), q["answer"],
                          list(zip(LETTERS, q["options"])))))

    h.append(part_bar(4, "Questions 16–20 · the missing words"))
    h.append(rubric(R4["intro"]))
    h.append(panel([("<b>%s</b>" % E(R4["title"])), E(R4["text"])], fill="#fff"))
    for g in R4["gaps"]:
        h.append(item(g["q"], "",
                      ask("mcq", "Gap %d" % g["q"], g["answer"],
                          list(zip(LETTERS, g["options"])))))

    h.append(part_bar(5, "Questions 21–25 · one word in each gap"))
    h.append(rubric(R5["intro"]))
    h.append(panel([("<b>%s</b>" % E(R5["title"]))] +
                   [E(p) for p in R5["text"].split("\n") if p.strip()],
                   fill="#fff"))
    for g in R5["gaps"]:
        h.append(item(g["q"], "Write ONE word for gap %d." % g["q"],
                      ask("typed", "Gap %d" % g["q"], g["answer"])))

    h.append(part_bar("W1", "Writing · a short email"))
    h.append(rubric(paper.WRITING1["task"]))
    h.append(panel(["&bull; " + E(p) for p in paper.WRITING1["points"]]))
    h.append(rubric(paper.WRITING1["words"]))
    h.append('<p>%s</p>' % ask("open", "Question 1 · the short email", None))

    h.append(part_bar("W2", "Writing · giving advice"))
    h.append(rubric(paper.WRITING2["task"]))
    h.append(panel([E(paper.WRITING2["quote"])], fill="#fff"))
    h.append(rubric(paper.WRITING2["words"]))
    h.append('<p>%s</p>' % ask("open", "Question 2 · the advice email", None))

    return '<div class="booklet">%s</div>' % "".join(h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("level", choices=sorted(PAPERS),
                    help="which Competency paper to build")
    ap.add_argument("--paper", action="store_true")
    ap.add_argument("--digital", action="store_true")
    ap.add_argument("--out", default="")
    ap.add_argument("--minutes", type=int, default=60)
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--resittable", action="store_true",
                    help="let students sit it more than once")
    ap.add_argument("--upload", action="store_true")
    ap.add_argument("--site",
                    default="https://ielts-tracker-production.up.railway.app")
    args = ap.parse_args()

    module, level_line, name = PAPERS[args.level]
    global paper, LEVEL_LINE, DIGITAL_HEAD
    paper = __import__(module)
    LEVEL_LINE = level_line
    DIGITAL_HEAD = level_line.upper() + " \u00b7 MOCK FINAL"
    site_level = "Pre-Intermediate" if args.level == "b1" else "Intermediate"
    out = os.path.expanduser(args.out or ("~/Desktop/%s" % name))

    if args.paper:
        os.makedirs(out, exist_ok=True)
        import export_booklet as ex
        for label, inner in (
                ("%s - Question paper" % name,
                 listening_html() + reading_html() + writing_html()),
                ("%s - Answer key" % name, key_html()),
                ("%s - Audioscript" % name, script_html())):
            ex.to_pdf(page(label, inner), os.path.join(out, label + ".pdf"))
            ex.to_docx(inner, os.path.join(out, label + ".docx"), label)
            print("   %-42s written" % label)

    if args.digital:
        layout = digital_layout()
        marked = sum(1 for q in QS if q["kind"] != "open")
        data = {"level": site_level, "number": 98,
                "title": "%s \u2014 Reading and Writing" % name,
                "passages": {}, "layout": layout, "questions": QS,
                "minutes": args.minutes, "strict": bool(args.strict),
                "once": not args.resittable}
        dest = os.path.join(HERE, "%s_mock_digital.json" % args.level)
        json.dump(data, open(dest, "w"))
        print("%s \u00b7 %d questions (%d marked, 2 written) \u00b7 %d minutes "
              "\u00b7 %s \u00b7 %s"
              % (site_level, len(QS), marked, args.minutes,
                 "leaving the page hands it in" if args.strict
                 else "no window rule",
                 "resittable" if args.resittable else "one sitting"))
        print("written to", dest)
        if args.upload:
            import upload_booklets as ub
            password = os.environ.get("TEACHER_PASSWORD", "")
            if not password:
                sys.exit("Set TEACHER_PASSWORD first.")
            opener = ub.sign_in(args.site, password)
            print("sent:", ub.post_json(opener, args.site, dest))


if __name__ == "__main__":
    main()
