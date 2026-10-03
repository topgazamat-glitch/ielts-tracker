"""The bugs found in the sweep of 3 October 2026, each held to its fix.

A handout's key changed on the site is marked by the new key at once; work
photographed on time and picked up by the morning rescue is on time; a typed
essay tells the teacher; an upload refused as already sent says so; a student's
page that breaks shows a page and tells the teacher; a mark saved twice is sent
once; a booklet set as homework says why it cannot be deleted; the stylesheet
travels gzipped and named by its version.

Run me with:  python3 run_tests.py sweep
"""
import gzip
import json
import os
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import http.cookiejar

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None)
json.dump({"teacher_password": "pw", "automation": False}, open(os.path.join(tmp, "config.json"), "w"))

import core
import server
import bot
import jobs
from datetime import timedelta

core.init_db(); db = core.connect()
now = core.iso(core.now())

fails, checks = [], 0


def check(what, cond):
    global checks
    checks += 1
    print(("  ok  " if cond else "  FAIL") + "  " + what)
    if not cond:
        fails.append(what)


lvl = db.execute("SELECT id FROM levels WHERE name='Pre-Intermediate'").fetchone()["id"]
g = db.execute("INSERT INTO groups (name, join_code, created_at, level_id) VALUES ('214','SW1',?,?)",
               (now, lvl)).lastrowid
sid = core.add_student(db, "Iroda", g)
tok = db.execute("SELECT token FROM students WHERE id=?", (sid,)).fetchone()["token"]
db.execute("UPDATE students SET telegram_id=777 WHERE id=?", (sid,))
db.commit()

print("1. A KEY CHANGED ON THE SITE MARKS BY THE NEW KEY AT ONCE")
layout = ('<div class="booklet"><h2 class="bk-part">Part 1</h2>'
          '<p>1 <input class="bk-blank" data-q="1"></p>'
          '<p>2 <input class="bk-blank" data-q="2"></p></div>')
hid = core.load_test(db, {"level": "Pre-Intermediate", "number": 1, "title": "Unit 1",
                          "kind": "handout", "layout": layout, "passages": {},
                          "questions": [{"num": 1, "kind": "typed", "prompt": "a", "answer": "cat"},
                                        {"num": 2, "kind": "typed", "prompt": "b", "answer": None}]})
db.execute("UPDATE dtests SET published=1 WHERE id=?", (hid,)); db.commit()
q1, q2 = [r["id"] for r in db.execute("SELECT id FROM dquestions WHERE test_id=? ORDER BY num", (hid,))]
aid = core.start_attempt(db, hid, sid)
db.execute("INSERT INTO dresponses (attempt_id, question_id, given, correct) VALUES (?,?,?,1)", (aid, q1, "cat"))
db.execute("INSERT INTO dresponses (attempt_id, question_id, given, correct) VALUES (?,?,?,0)", (aid, q2, "dgo"))
parts = core.handout_info(db, hid)["parts"]
for p in parts:
    db.execute("INSERT INTO dparts (attempt_id, part, checked_at) VALUES (?,?,?)", (aid, p, now))
db.commit()
before = core.handout_status(db, hid, sid)["mark"]
core.set_answer_key(db, hid, {q2: "dog"})
after = core.handout_status(db, hid, sid)["mark"]
print("   mark with one box keyed: %s, with both keyed: %s" % (before, after))
check("the second box now counts against the mark", after < before)

print("\n2. WORK PHOTOGRAPHED ON TIME AND PICKED UP BY THE RESCUE IS ON TIME")
hw = db.execute("INSERT INTO assignments (group_id, title, due_at, created_at, published)"
                " VALUES (?,?,?,?,1)", (g, "Essay", core.iso(core.now() - timedelta(hours=10)),
                                         now)).lastrowid
sent_at = core.now() - timedelta(hours=12)          # two hours before the deadline
sub = db.execute("INSERT INTO submissions (student_id, assignment_id, created_at, draft)"
                 " VALUES (?,?,?,1)", (sid, hw, core.iso(sent_at))).lastrowid
db.execute("INSERT INTO files (submission_id, filename, ord) VALUES (?,?,0)",
           (sub, "%d_0_%d.jpg" % (sub, int(sent_at.timestamp()))))
db.commit()
bot.notify_teachers_new = lambda *a, **k: 0
jobs._send = lambda *a, **k: None
jobs.rescue_drafts(db, "TOKEN", {"draft_hours": 2})
row = db.execute("SELECT draft, created_at FROM submissions WHERE id=?", (sub,)).fetchone()
due = db.execute("SELECT due_at FROM assignments WHERE id=?", (hw,)).fetchone()["due_at"]
print("   sent %s, deadline %s" % (row["created_at"], due))
check("the rescued work is handed in", row["draft"] == 0)
check("and counts as sent before the deadline", row["created_at"] <= due)

print("\n3. A TYPED ESSAY TELLS THE TEACHERS THE BOT KNOWS")
told = []
bot.send = lambda token, chat, text, *a, **k: told.append((str(chat), text))
core.meta_set(db, "teachers", json.dumps(["555"]))
server.CFG["telegram_token"] = "TOKEN"
wsub = db.execute("INSERT INTO submissions (student_id, assignment_id, created_at, kind, words)"
                  " VALUES (?,?,?,'text',120)", (sid, hw, now)).lastrowid
db.commit()
server.notify_handed_in(db, wsub)
print("   messages:", told)
check("the teacher is told", told and told[0][0] == "555" and "typed 120 words" in told[0][1])
server.CFG["telegram_token"] = ""

# ---- over HTTP from here on
srv = server.Server(("127.0.0.1", 0), server.Handler)
port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
base = "http://127.0.0.1:%d" % port
plain = urllib.request.build_opener()


def fetch(op, path, data=None, headers=None):
    req = urllib.request.Request(base + path, data=data, headers=headers or {})
    try:
        r = op.open(req, timeout=20)
        return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()


print("\n4. AN UPLOAD REFUSED AS ALREADY SENT SAYS SO")
code, _h, body = fetch(plain, "/s/%s?e=locked" % tok)
check("the page explains it", b"already been sent" in body)

print("\n5. A STUDENT'S PAGE THAT BREAKS SHOWS A PAGE AND TELLS THE TEACHER")
reported = []
real_report, real_portal = core.report_breakage, server.view_student_portal
core.report_breakage = lambda where, exc: reported.append((where, str(exc)))


def explode(*a, **k):
    raise RuntimeError("boom")


server.view_student_portal = explode
code, _h, body = fetch(plain, "/s/%s?tab=home" % tok)
server.view_student_portal = real_portal
core.report_breakage = real_report
print("   status %s, reported %s" % (code, reported))
check("the student gets a page, not a dropped connection", code == 500 and b"Something went wrong" in body)
check("the teacher is told, without the student's link", reported and tok not in reported[0][0]
      and reported[0][1] == "boom")

jar = http.cookiejar.CookieJar()
teacher = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
fetch(teacher, "/login", urllib.parse.urlencode({"password": "pw"}).encode())

print("\n6. A MARK SAVED TWICE IS SENT TO THE STUDENT ONCE")
notified = []
server.notify_later = lambda fn, *a: notified.append(a)
psub = db.execute("INSERT INTO submissions (student_id, assignment_id, created_at)"
                  " VALUES (?,?,?)", (sid, hw, now)).lastrowid
db.commit()
form = urllib.parse.urlencode({"submission_id": psub, "score": "7", "note": ""}).encode()
fetch(teacher, "/grade", form)
fetch(teacher, "/grade", form)
graded = db.execute("SELECT status, score FROM submissions WHERE id=?", (psub,)).fetchone()
print("   saved: %s %s, messages: %d" % (graded["status"], graded["score"], len(notified)))
check("the mark is saved", graded["status"] == "graded" and graded["score"] == 7)
check("and sent once", len(notified) == 1)
fetch(teacher, "/grade", urllib.parse.urlencode({"submission_id": psub, "score": "8"}).encode())
check("a changed mark is sent again", len(notified) == 2)

print("\n7. A BOOKLET SET AS HOMEWORK SAYS WHY IT CANNOT BE DELETED")
db.execute("INSERT INTO assignments (group_id, title, test_id, due_at, created_at, published)"
           " VALUES (?,?,?,?,?,1)", (g, "Unit 1 handout", hid, now, now))
db.commit()
code, _h, body = fetch(teacher, "/tests/%d/delete" % hid, b"")
still = db.execute("SELECT 1 FROM dtests WHERE id=?", (hid,)).fetchone()
check("no error page", b"Something broke" not in body)
check("it names the homework that holds it", b"Not deleted" in body and b"Unit 1 handout" in body)
check("and the booklet is still there", bool(still))

print("\n8. THE STYLESHEET TRAVELS GZIPPED AND NAMED BY ITS VERSION")
code, _h, body = fetch(plain, "/s/%s" % tok)
v = server.STATIC_V
check("pages name it with the version", ("/static/style.css?v=%s" % v).encode() in body)
code, h, body = fetch(plain, "/static/style.css?v=%s" % v, headers={"Accept-Encoding": "gzip"})
real = open(os.path.join(ROOT, "static", "style.css"), "rb").read()
check("it is kept for a year", "immutable" in h.get("Cache-Control", ""))
check("it is gzipped", h.get("Content-Encoding") == "gzip" and gzip.decompress(body) == real)
code, h, body = fetch(plain, "/static/style.css")
check("a bare name is kept five minutes, as before", h.get("Cache-Control") == "max-age=300"
      and body == real)

print("\n%d checks, %d failed" % (checks, len(fails)))
sys.exit(1 if fails else 0)
