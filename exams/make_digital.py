"""Turn the mock's Reading and Writing paper into a test on the website.

The same content file the printed paper comes from, laid out as a page a
student sits: options are chosen rather than typed, the open cloze and the
note gaps are boxes, and the email is a proper writing box. Everything is
numbered the way the paper is, so a student can be told "question 14" and find
it.

    export TEACHER_PASSWORD='...'
    python3 exams/make_digital.py --minutes 50 --strict --upload
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
import a2_mock_final as paper   # replaced by --paper; see main()

E = html.escape
TEAL, DEEP, GREY, RULE = "#127D80", "#0B5456", "#6E6E6E", "#C9C9C9"
QS = []


def ask(kind, prompt, answer, options=None):
    """One numbered question; returns the marker to drop into the page."""
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


def build():
    R1, R2, R3 = paper.R_PART1, paper.R_PART2, paper.R_PART3
    R4, R5 = paper.R_PART4, paper.R_PART5
    h = [head("A2 KEY · MOCK FINAL", 9, TEAL, 2),
         head("Reading and Writing", 20),
         rubric("Five parts, twenty-five questions, and one email. "
                "Answer every question — a wrong answer costs nothing.")]

    h.append(part_bar(1, "Questions 1–5 · the notices"))
    h.append(rubric(R1["intro"]))
    h.append(panel(["<b>%s</b> &nbsp;%s" % (L, E(t)) for L, t in R1["notices"]]))
    # Only the letters: the notices are in the panel above, and repeating all
    # eight of them under each of the five questions is forty lines of reading
    # for one choice.
    letters = [(L, "") for L, _t in R1["notices"]]
    for n, text, ans in R1["items"]:
        h.append(item(n, E(text), ask("mcq", "%d %s" % (n, text), ans, letters)))

    h.append(part_bar(2, "Questions 6–10 · the right word"))
    h.append(rubric(R2["intro"]))
    for n, stem, opts, ans in R2["items"]:
        h.append(item(n, E(stem),
                      ask("mcq", "%d %s" % (n, stem), ans,
                          list(zip("ABC", opts)))))

    h.append(part_bar(3, "Questions 11–15 · the article"))
    h.append(rubric(R3["intro"]))
    h.append(panel([("<b>%s</b>" % E(R3["title"]))] +
                   [E(p) for p in R3["text"]], fill="#fff"))
    for q in R3["questions"]:
        h.append(item(q["q"], E(q["stem"]),
                      ask("mcq", "%d %s" % (q["q"], q["stem"]), q["answer"],
                          list(zip("ABC", q["options"])))))

    h.append(part_bar(4, "Questions 16–20 · the grammar"))
    h.append(rubric(R4["intro"]))
    h.append(panel([("<b>%s</b>" % E(R4["title"])), E(R4["text"])], fill="#fff"))
    for n, opts, ans in R4["items"]:
        h.append(item(n, "",
                      ask("mcq", "Gap %d" % n, ans, list(zip("ABC", opts)))))

    h.append(part_bar(5, "Questions 21–25 · one word in each gap"))
    h.append(rubric(R5["intro"]))
    for greeting, body, sign in R5["letters"]:
        h.append(panel([("<b>%s</b>" % E(greeting)), E(body),
                        E(sign).replace("\n", "<br>")], fill="#fff"))
    for n in sorted(R5["answers"]):
        h.append(item(n, "Write ONE word for gap %d." % n,
                      ask("typed", "Gap %d" % n, R5["answers"][n])))

    h.append(part_bar("W", "Writing · an email"))
    h.append(rubric(paper.WRITING["task"]))
    h.append(panel(["&bull; " + E(p) for p in paper.WRITING["points"]]))
    h.append(rubric(paper.WRITING["words"]))
    h.append('<p>%s</p>' % ask("open", "The email", None))

    return '<div class="booklet">%s</div>' % "".join(h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paper", default="a2_mock_final",
                    help="the content module, e.g. a2_mock_2")
    ap.add_argument("--minutes", type=int, default=50)
    ap.add_argument("--strict", action="store_true",
                    help="leaving the page hands the paper in")
    ap.add_argument("--level", default="Elementary")
    ap.add_argument("--title", default="A2 Mock Final — Reading and Writing")
    ap.add_argument("--out", default="")
    ap.add_argument("--upload", action="store_true")
    ap.add_argument("--site",
                    default="https://ielts-tracker-production.up.railway.app")
    args = ap.parse_args()

    global paper, QS
    paper = __import__(args.paper)
    QS = []
    layout = build()
    marked = sum(1 for q in QS if q["kind"] != "open")
    data = {"level": args.level, "number": 99, "title": args.title,
            "passages": {}, "layout": layout, "questions": QS,
            "minutes": args.minutes, "strict": bool(args.strict)}
    out = args.out or os.path.join(HERE, "%s_digital.json" % args.paper)
    json.dump(data, open(out, "w"))
    print("%d questions (%d marked, 1 email) · %d minutes · %s"
          % (len(QS), marked, args.minutes,
             "leaving the page ends it" if args.strict else "no window rule"))
    print("written to", out)

    if args.upload:
        import upload_booklets as ub
        import upload_tests  # noqa: F401  (shares the sign-in)
        password = os.environ.get("TEACHER_PASSWORD", "")
        if not password:
            sys.exit("Set TEACHER_PASSWORD first.")
        opener = ub.sign_in(args.site, password)
        print("sent:", ub.post_json(opener, args.site, out))


if __name__ == "__main__":
    main()
