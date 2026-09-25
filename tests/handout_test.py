"""Handouts: a booklet a student works through, and marks themselves.

The two things that matter. What they type must survive closing the page,
because they work on a phone on a bus. And the marking must be honest: right
is right, wrong is wrong, and a sentence of their own is neither.

Run me with:  python3 run_tests.py handout
"""
import json
import os
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

layout = ('<div class="booklet"><p>1 <input class="bk-blank" data-q="1"></p>'
          '<p>2 <input class="bk-blank" data-q="2"></p>'
          '<p>3 <input class="bk-blank" data-q="3"></p></div>')
hid = core.load_test(db, {
    "level": "Pre-Intermediate", "number": 2, "title": "Unit 2A & 2C",
    "kind": "handout", "layout": layout, "passages": {},
    "questions": [
        {"num": 1, "kind": "typed", "prompt": "1.1 a", "answer": "airport"},
        {"num": 2, "kind": "typed", "prompt": "1.1 b", "answer": "by plane / plane"},
        {"num": 3, "kind": "open", "prompt": "1.2 tell a partner", "answer": None},
    ]})
db.execute("UPDATE dtests SET published=1 WHERE id=?", (hid,))
# a real test, to prove the two do not mix
tid = core.load_test(db, {"level": "Pre-Intermediate", "number": 9,
                          "title": "A real test", "layout": layout,
                          "passages": {}, "questions": []})
db.execute("UPDATE dtests SET published=1 WHERE id=?", (tid,))
db.commit()

qids = [r["id"] for r in db.execute(
    "SELECT id FROM dquestions WHERE test_id=? ORDER BY num", (hid,))]

fails, checks = [], 0


def check(what, cond):
    global checks
    checks += 1
    print(("  ok  " if cond else "  FAIL") + "  " + what)
    if not cond:
        fails.append(what)


import html as _html
import threading, time, urllib.request, urllib.parse
srv = server.Server(("127.0.0.1", 8841), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
time.sleep(0.4)
base = "http://127.0.0.1:8841"
op = urllib.request.build_opener()


def get(path):
    # unescaped, because a title with an & in it arrives as &amp;
    return _html.unescape(op.open(base + path, timeout=20).read().decode())


def post(path, fields):
    return json.loads(op.open(base + path,
                              urllib.parse.urlencode(fields).encode(),
                              timeout=20).read().decode())


# ------------------------------------------------------- the two are separate
page = get("/s/%s?tab=handouts" % tok)
check("the Handouts tab exists", "Handouts" in page)
check("the booklet is listed", "Unit 2A & 2C" in page)
check("a real test is not on the Handouts page", "A real test" not in page)
tests_page = get("/s/%s?tab=tests" % tok)
check("the booklet is not on the Tests page", "Unit 2A & 2C" not in tests_page)
check("the real test still is", "A real test" in tests_page)

book = get("/s/%s?tab=handouts&h=%d" % (tok, hid))
check("the booklet opens with its boxes", book.count('name="q') == 3)
check("there is a check button", "checkbtn" in book)
check("and no clock", "minutes" not in book.lower() or "clock" not in book.lower())

# ------------------------------------------------------------------ saving
post("/s/%s/handout/%d/save" % (tok, hid), {"q%d" % qids[0]: "  Airport "})
again = get("/s/%s?tab=handouts&h=%d" % (tok, hid))
check("what they typed comes back", "Airport" in again)

# ------------------------------------------------------------------ marking
out = post("/s/%s/handout/%d/check" % (tok, hid),
           {"q%d" % qids[0]: "airport",
            "q%d" % qids[1]: "helicopter",
            "q%d" % qids[2]: "I went to Samarkand with my cousin."})
m = out["marks"]
check("a right answer is marked right", m[str(qids[0])]["state"] == "right")
check("a wrong answer is marked wrong", m[str(qids[1])]["state"] == "wrong")
check("and the answer is there to reveal",
      m[str(qids[1])]["answer"] == "by plane / plane")
check("a right answer does not leak the key",
      m[str(qids[0])].get("answer") is None)
check("their own sentence is for the teacher, not wrong",
      m[str(qids[2])]["state"] == "teacher")
check("the tally counts only what can be marked",
      out["right"] == 1 and out["wrong"] == 1 and out["teacher"] == 1)

out = post("/s/%s/handout/%d/check" % (tok, hid),
           {"q%d" % qids[0]: "  AIRPORT.  "})
check("marking forgives case, spaces and a full stop",
      out["marks"][str(qids[0])]["state"] == "right")
out = post("/s/%s/handout/%d/check" % (tok, hid),
           {"q%d" % qids[1]: "plane"})
check("either of two answers is accepted",
      out["marks"][str(qids[1])]["state"] == "right")
out = post("/s/%s/handout/%d/check" % (tok, hid), {"q%d" % qids[0]: ""})
check("an empty box is not marked wrong",
      str(qids[0]) not in out["marks"] and out["blank"] >= 1)

check("the marks are kept", db.execute(
    "SELECT correct FROM dresponses r JOIN dattempts a ON a.id=r.attempt_id"
    " WHERE a.test_id=? AND r.question_id=?", (hid, qids[1])).fetchone()[0] == 1)
check("nothing was handed in", db.execute(
    "SELECT finished_at FROM dattempts WHERE test_id=?", (hid,)).fetchone()[0] is None)

# ------------------------------------------------------------- not a free-for-all
other = core.add_student(db, "Someone else", g)
otok = db.execute("SELECT token FROM students WHERE id=?", (other,)).fetchone()["token"]
post("/s/%s/handout/%d/save" % (otok, hid), {"q%d" % qids[0]: "mine"})
mine = get("/s/%s?tab=handouts&h=%d" % (tok, hid))
check("one student cannot see another's answers", "mine" not in mine)
bad = json.loads(op.open(base + "/s/nosuchtoken/handout/%d/check" % hid,
                         b"", timeout=20).read().decode())
check("a stranger cannot mark anything", bad.get("ok") is False)
srv.shutdown()

print()
print("handout: %d checks, %d failed" % (checks, len(fails)))
sys.exit(1 if fails else 0)
