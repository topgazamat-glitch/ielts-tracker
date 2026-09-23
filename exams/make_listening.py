"""Turn a mock's Listening paper into a test on the website.

The recording is uploaded once as a material, and the test page plays it.
The parts are laid out the way the paper is: five short conversations,
a matching task, a longer conversation, and notes to complete.

A student hears the recording through the page, so there is nothing to hand
out and nothing to play in class. The clock is the site's, as it is for the
reading paper.

    export TEACHER_PASSWORD='...'
    python3 exams/make_listening.py --paper a2_mock_2 \
        --audio ~/Desktop/"A2 Mock 2/A2 Mock 2 - Full listening.m4a" --upload
"""
import argparse
import html
import json
import mimetypes
import os
import sys
import urllib.parse
import urllib.request
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)

E = html.escape
TEAL, DEEP, GREY = "#127D80", "#0B5456", "#6E6E6E"
QS = []
paper = None


def ask(kind, prompt, answer, options=None):
    QS.append({"num": len(QS) + 1, "kind": kind, "prompt": prompt[:180],
               "answer": answer,
               "options": [{"letter": L, "text": t}
                           for L, t in (options or [])]})
    n = len(QS)
    if kind == "mcq":
        return '<span data-mcq="%d"></span>' % n
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


def player(track):
    """The recording.

    The page does not carry an <audio> tag of its own. The site already puts
    a player after any paragraph that names a track, and it adds the
    student's own link to the address, which a layout shared by the whole
    class cannot do. So the paragraph names the track and the site does the
    rest.
    """
    return ('<table class="bk"><tr><td style="background:%s;border:1px solid %s;'
            'padding:12px">'
            '<p style="margin:0 0 6px"><span style="font-weight:700;color:%s;'
            'font-size:11pt">The recording</span></p>'
            '<p style="margin:0 0 8px"><span style="font-size:10pt;color:%s">'
            'Put your headphones on and press play. Every part is heard twice '
            'on the recording, so do not go back to the beginning.</span></p>'
            '<p style="margin:0"><span style="font-size:10pt;color:%s">'
            'Listening, track %s</span></p>'
            '</td></tr></table>' % ("#F2F8F8", TEAL, DEEP, GREY, GREY, track))


def build(track):
    P1, P2, P3, P4 = paper.PART1, paper.PART2, paper.PART3, paper.PART4
    h = [head("A2 KEY · MOCK FINAL", 9, TEAL, 2),
         head("Listening", 20),
         rubric("Four parts, twenty questions. You will hear every part "
                "twice. Answer every question — a wrong answer costs "
                "nothing."),
         player(track)]

    h.append(part_bar(1, "Questions 1–5 · five short conversations"))
    h.append(rubric("You will hear five short conversations. For each "
                    "question, choose A, B or C."))
    for c in P1:
        h.append(item(c["q"], E(c["ask"]),
                      ask("mcq", "%d %s" % (c["q"], c["ask"]), c["answer"],
                          list(zip("ABC", c["options"])))))

    h.append(part_bar(2, "Questions 6–10 · who does what"))
    h.append(rubric(P2["intro"]))
    h.append(panel(["<b>%s</b> &nbsp;%s" % (L, E(t)) for L, t in P2["options"]]))
    letters = [(L, "") for L, _t in P2["options"]]
    for num, who in P2["people"]:
        h.append(item(num, E(who),
                      ask("mcq", "%s %s" % (num, who), P2["answers"][num],
                          letters)))

    h.append(part_bar(3, "Questions 11–15 · a longer conversation"))
    h.append(rubric(P3["intro"]))
    for q in P3["questions"]:
        h.append(item(q["q"], E(q["stem"]),
                      ask("mcq", "%d %s" % (q["q"], q["stem"]), q["answer"],
                          list(zip("ABC", q["options"])))))

    h.append(part_bar(4, "Questions 16–20 · complete the notes"))
    h.append(rubric(P4["intro"]))
    h.append(panel([("<b>%s</b>" % E(P4["title"]))], fill="#fff"))
    for g in P4["gaps"]:
        h.append(item(g["q"], E(g["label"]),
                      ask("typed", "%d %s" % (g["q"], g["label"]),
                          str(g["answer"]))))

    return '<div class="booklet">%s</div>' % "".join(h)


def upload_track(opener, site, path, level, track):
    """Put the recording on the level's shelf, under its track number."""
    mime = mimetypes.guess_type(path)[0] or "audio/mp4"
    bound = "----ta" + uuid.uuid4().hex
    body = (('--%s\r\nContent-Disposition: form-data; name="level"\r\n\r\n%s\r\n'
             % (bound, level)).encode())
    body += (('--%s\r\nContent-Disposition: form-data; name="file"; '
              'filename="%s.m4a"\r\nContent-Type: %s\r\n\r\n'
              % (bound, track, mime)).encode())
    body += open(path, "rb").read()
    body += ("\r\n--%s--\r\n" % bound).encode()
    req = urllib.request.Request(
        site + "/audio/new", data=body,
        headers={"Content-Type": "multipart/form-data; boundary=" + bound})
    opener.open(req, timeout=900)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paper", default="a2_mock_2")
    ap.add_argument("--audio", default="", help="the recording to upload")
    ap.add_argument("--track", default="",
                    help="the track number to put it on, e.g. 99.01")
    ap.add_argument("--minutes", type=int, default=35)
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--level", default="Elementary")
    ap.add_argument("--title", default="")
    ap.add_argument("--out", default="")
    ap.add_argument("--upload", action="store_true")
    ap.add_argument("--site",
                    default="https://ielts-tracker-production.up.railway.app")
    args = ap.parse_args()

    global paper, QS
    paper = __import__(args.paper)
    QS = []
    title = args.title or (args.paper.replace("_", " ").title() + " — Listening")

    opener = None
    if not args.track:
        sys.exit("Give me --track, e.g. --track 99.01")
    if args.upload:
        import upload_booklets as ub
        password = os.environ.get("TEACHER_PASSWORD")
        if not password:
            sys.exit("Set TEACHER_PASSWORD first.")
        opener = ub.sign_in(args.site, password)
        if args.audio:
            if not os.path.exists(args.audio):
                sys.exit("No recording at %s" % args.audio)
            upload_track(opener, args.site, args.audio, args.level, args.track)
            print("recording is on %s track %s" % (args.level, args.track))

    layout = build(args.track)
    marked = sum(1 for q in QS if q["kind"] != "open")
    data = {"level": args.level, "number": 99, "title": title,
            "passages": {}, "layout": layout, "questions": QS,
            "minutes": args.minutes, "strict": bool(args.strict)}
    out = args.out or os.path.join(HERE, "%s_listening.json" % args.paper)
    json.dump(data, open(out, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("%d questions (%d marked) · %d minutes · %s"
          % (len(QS), marked, args.minutes,
             "leaving the page ends it" if args.strict else "no window rule"))
    print("written to", out)

    if args.upload:
        import upload_booklets as ub
        print("sent:", ub.post_json(opener, args.site, out))


if __name__ == "__main__":
    sys.exit(main())
