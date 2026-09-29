"""A student who joins the class later, and handouts a student is let off.

Homework whose deadline passed before a student joined their class is not
theirs: not in the league, not missed, and its handout does not hold up the
next one. The teacher can also let a student off any handout by hand. The
date a student joined is recorded when they are moved or join through the
bot, or set by the teacher - never guessed from when they were added.

Run me with:  python3 run_tests.py late_joiner
"""
import html as _html
import http.cookiejar
import os
import sys
import tempfile
import threading
import time
import urllib.parse
import urllib.request
from datetime import timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["DATA_DIR"] = tempfile.mkdtemp(); os.environ.pop("TELEGRAM_TOKEN", None)
os.environ["TEACHER_PASSWORD"] = "pw"
import core, server

db = core.init_db()
cfg = core.load_config()
now = core.now()
fails, checks = [], 0


def check(what, cond):
    global checks
    checks += 1
    print(("  ok  " if cond else "  FAIL") + "  " + what)
    if not cond:
        fails.append(what)


lvl = db.execute("SELECT id FROM levels WHERE name='Pre-Intermediate'").fetchone()["id"]
g = db.execute("INSERT INTO groups (name, join_code, created_at, level_id) VALUES ('214','A',?,?)",
               (core.iso(now - timedelta(days=60)), lvl)).lastrowid
g2 = db.execute("INSERT INTO groups (name, join_code, created_at, level_id) VALUES ('216','B',?,?)",
                (core.iso(now - timedelta(days=60)), lvl)).lastrowid
old = core.add_student(db, "Olim", g)            # here from the start
new = core.add_student(db, "Nodira", g)          # joins in week 5
layout = ('<div class="booklet"><table class="bk"><tr><td style="background:#%s"><p><span>1</span></p></td>'
          '<td><p><span>Part · one</span></p></td></tr></table><p><span>1  </span>'
          '<input class="bk-blank" data-q="1"></p></div>' % core.BOOKLET_TEAL)


def handout(n, title):
    tid = core.load_test(db, {"level": "Pre-Intermediate", "number": n, "title": title, "kind": "handout",
                              "layout": layout, "passages": {},
                              "questions": [{"num": 1, "kind": "typed", "prompt": "1.1  1", "answer": "went"}]})
    db.execute("UPDATE dtests SET published=1 WHERE id=?", (tid,))
    return tid


h1, h2, h5 = handout(1, "Unit 1A & 1C — One"), handout(2, "Unit 2A & 2C — Two"), handout(5, "Unit 5B & 5D — Five")


def set_hw(tid, title, due):
    return db.execute("INSERT INTO assignments (group_id, title, created_at, published, due_at, test_id)"
                      " VALUES (?,?,?,1,?,?)", (g, title, core.iso(due - timedelta(days=3)), core.iso(due),
                                                tid)).lastrowid


a1 = set_hw(h1, "Unit 1A & 1C — One", now - timedelta(days=30))
a2 = set_hw(h2, "Unit 2A & 2C — Two", now - timedelta(days=20))
a5 = set_hw(h5, "Unit 5B & 5D — Five", now + timedelta(days=2))
wb = db.execute("INSERT INTO assignments (group_id, title, created_at, published, due_at)"
                " VALUES (?,?,?,1,?)", (g, "Workbook unit 1 A&C", core.iso(now - timedelta(days=33)),
                                        core.iso(now - timedelta(days=30)))).lastrowid
db.commit()
st = lambda sid: db.execute("SELECT * FROM students WHERE id=?", (sid,)).fetchone()

print("1. WITH NO DATE, EVERYTHING IS THEIRS - AS BEFORE")
check("a student added to the site has no join date guessed for them", core.student_since(st(new)) is None)
check("so unit 5 is shut behind unit 1 for both",
      core.handout_blocked_by(db, h5, st(old))["id"] == h1 and core.handout_blocked_by(db, h5, st(new))["id"] == h1)

srv = server.Server(("127.0.0.1", 8897), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
time.sleep(0.4)
base = "http://127.0.0.1:8897"
jar = http.cookiejar.CookieJar()
teacher = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
teacher.open(base + "/login", urllib.parse.urlencode({"password": "pw"}).encode()).read()


def get(path):
    return _html.unescape(teacher.open(base + path, timeout=30).read().decode())


def post(path, fields):
    return teacher.open(base + path, urllib.parse.urlencode(fields).encode(), timeout=30).geturl()


print("\n2. THE TEACHER SAYS WHEN NODIRA JOINED")
joined = core.local_day(now - timedelta(days=10), cfg)
post("/students/%d/since" % new, {"since": joined})
check("the date is kept", core.local_day(core.parse(core.student_since(st(new))), cfg) == joined)
check("units 1 and 2 were due before she came: unit 5 is open to her",
      core.handout_blocked_by(db, h5, st(new)) is None)
check("but still shut for Olim, who was here", core.handout_blocked_by(db, h5, st(old)) is not None)
scores, late, missing, waiting, pending, batches = core.homework_marks(
    db, st(new), core.iso(now - timedelta(days=60)), core.iso(now), [])
check("the league does not count what was due before she came", missing == 0 and scores == [])
scores_o, _l, missing_o, *_r = core.homework_marks(db, st(old), core.iso(now - timedelta(days=60)),
                                                     core.iso(now), [])
check("Olim missed them, and the league says so", missing_o == 3)
check("her average and her record leave them out", core.student_stats(db, new)["average"] is None
      and all(t["assignment_id"] not in (a1, a2, wb) for t in core.student_stats(db, new)["timeline"]))
check("her completion is over what she owes: unit 5, not started", core.live_completion(db, new) == 0)
page = get("/students/%d" % new)
check("her page says which were before she joined", "before they joined" in page and "Unit 5B & 5D" in page)

print("\n3. THE TEACHER LETS OLIM OFF UNITS 1 AND 2")
post("/students/%d/excuse" % old, {"test_id": h1, "on": "1"})
check("let off unit 1: unit 2 now holds unit 5", core.handout_blocked_by(db, h5, st(old))["id"] == h2)
post("/students/%d/excuse" % old, {"test_id": h2, "on": "1"})
check("let off unit 2 as well: unit 5 is open", core.handout_blocked_by(db, h5, st(old)) is None)
scores_o, _l, missing_o, *_r = core.homework_marks(db, st(old), core.iso(now - timedelta(days=60)),
                                                     core.iso(now), [])
check("the league no longer counts them - only the workbook he missed", missing_o == 1)
check("his page says he was let off, with a way back", "let off" in get("/students/%d" % old)
      and "Make them do it" in get("/students/%d" % old))
check("the handouts he was let off stay open to practise",
      core.handout_open_to(db, h1, g) and any(b["id"] == h1 for b, _f in core.handout_shelf(db, st(old))))
post("/students/%d/excuse" % old, {"test_id": h2, "on": "0"})
check("made to do unit 2 again, it holds unit 5 again", core.handout_blocked_by(db, h5, st(old))["id"] == h2)

print("\n4. ON THEIR HOMEWORK LIST")
items = core.homework_items(db, g, db.execute("SELECT due_at FROM assignments WHERE id=?", (a1,)).fetchone()[0])
prog = core.set_progress(db, old, items)
check("a piece they were let off is not to do; the workbook still is",
      a1 in prog["excused_ids"] and prog["total"] == 1 and prog["remaining"][0]["id"] == wb)

print("\n5. MOVED TO ANOTHER CLASS, THE DATE IS KEPT BY ITSELF")
post("/students/%d/update" % old, {"name": "Olim", "group_id": g})          # the same class: no move
check("saving him in the same class is not a move", core.student_since(st(old)) is None)
post("/students/%d/update" % old, {"name": "Olim", "group_id": g2})
check("moving him records the day", core.student_since(st(old)) is not None)
srv.shutdown()

print()
print("late_joiner: %d checks, %d failed" % (checks, len(fails)))
sys.exit(1 if fails else 0)
