"""A handout on a phone: every box is answered the way a thumb can answer it.

The paper design is kept; what the student gets is a control per box. This
test builds a small handout with one of each kind of box and checks the page
a student opens, and that the marking still reads what those controls send.

Run me with:  python3 run_tests.py handout_phone
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import tempfile
tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None)

import core, server
core.init_db(); db = core.connect()
now = core.iso(core.now())

lvl = db.execute("SELECT id FROM levels WHERE name='Pre-Intermediate'").fetchone()["id"]
g = db.execute("INSERT INTO groups (name, join_code, created_at, level_id)"
               " VALUES ('214','X',?,?)", (now, lvl)).lastrowid
sid = core.add_student(db, "Iroda", g)
tok = db.execute("SELECT token FROM students WHERE id=?", (sid,)).fetchone()["token"]

TEAL = "#" + server.BOOKLET_TEAL
EX = '<p><span style="font-weight:700;color:%s;font-size:12pt">%s  </span><span>%s</span></p>'


def box(n, width="60px", hint=""):
    return ('<input class="bk-blank" data-q="%d" style="width:%s"%s>'
            % (n, width, ' placeholder="%s"' % hint if hint else ""))


def item(label, n, inner):
    return '<p data-item="%s:%d"><span>%d  </span><span>%s</span></p>' % (label, n, n, inner)


layout = (
    '<div class="booklet">'
    '<table class="bk"><tr><td style="background:%s"><p><span>1</span></p></td>'
    '<td><p><span>Reading</span></p></td></tr></table>' % TEAL
    + EX % (TEAL, "1.1", "Which day?")
    # two columns whose items run down: 1 | 3 over 2 | 4
    + '<table class="bk"><tr><td>%s</td><td>%s</td></tr><tr><td>%s</td><td>%s</td></tr></table>'
    % (item("1.1", 1, "a " + box(1)), item("1.1", 3, "c " + box(3)),
       item("1.1", 2, "b " + box(2)), item("1.1", 4, "d " + box(4)))
    + EX % (TEAL, "1.2", "Complete with a word from the box.")
    + '<table class="bk"><tr><td style="background:#E8F1F1"><p>arrived</p></td>'
      '<td style="background:#E8F1F1"><p>went</p></td>'
      '<td style="background:#E8F1F1"><p>saw</p></td></tr></table>'
    + item("1.2", 1, "I " + box(5, "120px") + " to Samarkand.")
    + EX % (TEAL, "1.3", "Correct the mistake.")
    + item("1.3", 1, "Did it was hot? " + box(6, "95%"))
    + EX % (TEAL, "1.4", "Write an email.")
    + '<p>' + box(7, "95%", "Write your email here") + '</p>'
    + EX % (TEAL, "1.5", "True or false? Correct the false ones.")
    + item("1.5", 1, "He hated it. " + box(8) + " " + box(9, "95%", "If it is false, correct it"))
    + EX % (TEAL, "1.6", "Put them in order.")
    + item("1.6", 1, box(10) + " He slept badly.")
    + '<p>' + box(11) + ' I checked my spelling.</p>'
    + '</div>')

DAY = [{"letter": d, "text": "Day " + d} for d in "123"]
hid = core.load_test(db, {
    "level": "Pre-Intermediate", "number": 2, "title": "Unit 2A & 2C",
    "kind": "handout", "layout": layout, "passages": {},
    "questions": [
        {"num": 1, "kind": "typed", "prompt": "1.1 a", "answer": "3", "options": DAY},
        {"num": 2, "kind": "typed", "prompt": "1.1 b", "answer": "2", "options": DAY},
        {"num": 3, "kind": "typed", "prompt": "1.1 c", "answer": "1", "options": DAY},
        {"num": 4, "kind": "typed", "prompt": "1.1 d", "answer": "2", "options": DAY},
        {"num": 5, "kind": "typed", "prompt": "1.2 1", "answer": "went"},
        {"num": 6, "kind": "typed", "prompt": "1.3 1", "answer": "Was it hot", "control": "tickfill"},
        {"num": 7, "kind": "open", "prompt": "1.4", "answer": None, "control": "essay"},
        {"num": 8, "kind": "typed", "prompt": "1.5 1", "answer": "F",
         "options": [{"letter": "T", "text": ""}, {"letter": "F", "text": ""}]},
        {"num": 9, "kind": "open", "prompt": "1.5 1 fix", "answer": None, "control": "note"},
        {"num": 10, "kind": "typed", "prompt": "1.6 1", "answer": "1", "control": "number"},
        {"num": 11, "kind": "open", "prompt": "check", "answer": None, "control": "tick"},
    ]})
db.execute("UPDATE dtests SET published=1 WHERE id=?", (hid,))
db.commit()
qid = {r["num"]: r["id"] for r in db.execute(
    "SELECT id, num FROM dquestions WHERE test_id=?", (hid,))}

fails, checks = [], 0


def check(what, cond):
    global checks
    checks += 1
    print(("  ok  " if cond else "  FAIL") + "  " + what)
    if not cond:
        fails.append(what)


import threading, time, urllib.request, urllib.parse
srv = server.Server(("127.0.0.1", 8842), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
time.sleep(0.4)
base = "http://127.0.0.1:8842"
op = urllib.request.build_opener()


def get(path):
    return op.open(base + path, timeout=20).read().decode()


def post(path, fields):
    return json.loads(op.open(base + path, urllib.parse.urlencode(fields).encode(),
                              timeout=20).read().decode())


page = get("/s/%s?tab=handouts&h=%d" % (tok, hid))
sheet = page[page.index('class="booksheet handout'):]

print("1. A CHOICE IS TAPPED, NOT TYPED")
check("each choice question is a row of chips", sheet.count('<span class="bk-chips"') == 5)
check("a chip shows its label and sends its letter",
      'value="3"' in sheet and "<span>Day 3</span>" in sheet)
check("chips are radio buttons, one group per question",
      sheet.count('name="q%d" value=' % qid[1]) == 3)

print("2. A GAP STAYS IN ITS SENTENCE; A SENTENCE GETS A BOX THAT GROWS")
check("a short gap is still an inline box",
      re.search(r'<input class="bk-blank[^"]*" name="q%d"' % qid[5], sheet) is not None)
check("Enter moves on to the next box", 'enterkeyhint="next"' in sheet)
check("a correction is a growing box with 'it is correct' beside it",
      re.search(r'<textarea class="bk-blank bk-long" name="q%d"' % qid[6], sheet) is not None
      and 'class="bk-tickfill" data-q="6"' in sheet)
check("a number asks for the number keyboard",
      re.search(r'name="q%d"[^>]*inputmode="numeric"' % qid[10], sheet) is not None)

print("3. A PIECE OF WRITING HAS ROOM, A HINT AND A WORD COUNT")
essay = re.search(r'<textarea class="bk-blank bk-long bk-essay"[^>]*name="q%d"[^>]*>' % qid[7], sheet)
check("the email is a big box", essay is not None and 'rows="4"' in essay.group(0))
check("with the hint written in it", essay is not None
      and 'placeholder="Write your email here"' in essay.group(0))
check("and a word count under it", 'class="bk-words" data-q="7"' in sheet)

print("4. A BOX THAT MAY STAY EMPTY IS NOT COUNTED AS WORK LEFT")
note = re.search(r'<textarea[^>]*name="q%d"[^>]*>' % qid[9], sheet)
check("'correct the false ones' is optional", note is not None and "data-optional" in note.group(0))
check("and keeps its hint", note is not None and 'placeholder="If it is false, correct it"' in note.group(0))
check("a tick is a button, not a box to type a tick into",
      'class="bk-tick" data-q="11"' in sheet and 'type="hidden" name="q%d"' % qid[11] in sheet)

print("5. THE PAGE READS IN ORDER AND CAN BE NAVIGATED")
check("a two-column exercise is marked to stack 1, 2, 3, 4", "bk-colgrid" in sheet)
check("a box of words is marked to wrap, not to stack",
      '<table class="bk bk-wordbox" style="background:#E8F1F1">' in sheet)
check("every exercise has an anchor", all('id="ex-1-%d"' % n in sheet for n in range(1, 7)))
check("the Go to menu lists them under their section",
      'id="bkjump"' in page and '<optgroup label="1 Reading">' in page)
check("the count leaves out ticks and optional boxes: 9 to do",
      re.search(r'id="sbcount">0 of 9<', page) is not None)
check("the script is a file, so the page can be swapped in",
      "/static/handout.js" in page and "<script>" not in sheet.split("</main>")[0])

print("6. WHAT THE CONTROLS SEND IS MARKED")
out = post("/s/%s/handout/%d/check" % (tok, hid), {
    "q%d" % qid[1]: "3", "q%d" % qid[2]: "1",
    "q%d" % qid[5]: "went", "q%d" % qid[6]: "was it hot?",
    "q%d" % qid[8]: "F", "q%d" % qid[9]: "",
    "q%d" % qid[10]: "1", "q%d" % qid[11]: "✓"})
m = out["marks"]
check("a right chip is right", m[str(qid[1])]["state"] == "right")
check("a wrong chip is wrong, with the answer to reveal",
      m[str(qid[2])]["state"] == "wrong" and m[str(qid[2])]["answer"] == "2")
check("a correction is marked like any answer", m[str(qid[6])]["state"] == "right")
check("an empty optional box is neither wrong nor 'for your teacher'", str(qid[9]) not in m)
check("a tick goes to the teacher", m[str(qid[11])]["state"] == "teacher")
check("chips nobody tapped are counted as still empty", out["blank"] == 2)

print("7. BOTH HANDOUT BUILDERS CAN BE RUN BY HAND")
for script in ("p04bd_digital.py", "p02ac_digital.py"):
    check(script + " is there", os.path.exists(os.path.join(ROOT, "handouts", script)))
js = open(os.path.join(ROOT, "static", "handout.js")).read()
check("the page script skips optional boxes in the count", "data-optional" in js)
check("and counts words", "bk-essay" in js and "words" in js)
srv.shutdown()

print()
print("handout_phone: %d checks, %d failed" % (checks, len(fails)))
sys.exit(1 if fails else 0)
