"""No homework with a deadline in the past; a class can move up a level.

A deadline in the past closes the homework the moment it is set: students
never see it, and the league counts it as missed. The site refuses one -
for new homework, for homework set again, and for a deadline being moved -
while an old homework whose deadline is not changing can still be renamed.
And a class that finishes its book can be moved to the next level from its
own page.

Run me with:  python3 run_tests.py deadline_guard
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

tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None); os.environ["TEACHER_PASSWORD"] = "pw"
import core, server

core.init_db(); db = core.connect(); cfg = core.load_config()
now = core.iso(core.now())
el = db.execute("SELECT id FROM levels WHERE name='Elementary'").fetchone()["id"]
pre = db.execute("SELECT id FROM levels WHERE name='Pre-Intermediate'").fetchone()["id"]
g = db.execute("INSERT INTO groups (name, join_code, created_at, level_id) VALUES ('216','A',?,?)",
               (now, el)).lastrowid
sid = core.add_student(db, "Mumtozaxon", g)
tok = db.execute("SELECT token FROM students WHERE id=?", (sid,)).fetchone()["token"]
for level, title in (("Elementary", "Unit 12A & 12C — Travel"), ("Pre-Intermediate", "Unit 1A & 1C — Communication")):
    t = core.load_test(db, {"level": level, "number": 1, "title": title, "kind": "handout",
                            "layout": '<div class="booklet"><p>x</p></div>', "passages": {}, "questions": []})
    db.execute("UPDATE dtests SET published=1 WHERE id=?", (t,))
db.commit()

fails, checks = [], 0


def check(what, cond):
    global checks
    checks += 1
    print(("  ok  " if cond else "  FAIL") + "  " + what)
    if not cond:
        fails.append(what)


srv = server.Server(("127.0.0.1", 8845), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
time.sleep(0.4)
base = "http://127.0.0.1:8845"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(base + "/login", urllib.parse.urlencode({"password": "pw"}).encode()).read()


def post(path, fields):
    r = op.open(base + path, urllib.parse.urlencode(fields).encode(), timeout=20)
    return r.geturl(), _html.unescape(r.read().decode())


def get(path):
    return _html.unescape(op.open(base + path, timeout=20).read().decode())


def day(offset):
    return core.local_day(core.now() + timedelta(days=offset), cfg)


def count():
    return db.execute("SELECT COUNT(*) FROM assignments WHERE group_id=?", (g,)).fetchone()[0]


print("1. NEW HOMEWORK")
check("the date picker starts at today", 'name="due" min="%s"' % day(0) in get("/assignments"))
url, pg = post("/assignments/list", {"group_id": g, "items": "kitobdan 99 betgacha\nWriting — an email",
                                     "due": day(-27), "due_time": "23:59", "publish": "1"})
check("a deadline in the past sets nothing", count() == 0)
check("and says why", "That deadline has already passed" in pg)
check("with everything typed still in the form", "kitobdan 99 betgacha" in pg and "Writing — an email" in pg)
check("and the checkboxes as they were: open now, no Telegram",
      'name="publish" value="1" checked' in pg and 'name="announce" value="1" checked' not in pg)
url, pg = post("/assignments/list", {"group_id": g, "items": "kitobdan 99 betgacha", "due": day(0),
                                     "due_time": "00:00", "publish": "1"})
check("earlier today counts as past too", count() == 0 and "already passed" in pg)
post("/assignments/list", {"group_id": g, "items": "kitobdan 99 betgacha\nWriting — an email",
                           "due": day(3), "due_time": "23:59", "publish": "1"})
check("a deadline to come is set", count() == 2)
due = db.execute("SELECT due_at FROM assignments WHERE group_id=? LIMIT 1", (g,)).fetchone()["due_at"]

print("\n2. MOVING A DEADLINE")
setpage = "/homework/set?" + urllib.parse.urlencode({"group": g, "due": due})
url, pg = post("/assignments/batch/edit", {"group_id": g, "due": due, "new_due": day(-1),
                                           "new_time": "23:59", "back": setpage})
check("into the past is refused", db.execute("SELECT due_at FROM assignments WHERE group_id=? LIMIT 1",
                                             (g,)).fetchone()["due_at"] == due)
check("and the page says so", "Nothing was moved" in pg)
url, pg = post("/assignments/batch/edit", {"group_id": g, "due": due, "new_due": day(5),
                                           "new_time": "23:59", "back": setpage})
new_due = db.execute("SELECT due_at FROM assignments WHERE group_id=? LIMIT 1", (g,)).fetchone()["due_at"]
check("to a later day works", new_due != due and not core.deadline_passed(new_due))

print("\n3. AN OLD HOMEWORK CAN STILL BE RENAMED")
old = core.iso(core.now() - timedelta(days=20))
aid = db.execute("INSERT INTO assignments (group_id, title, created_at, due_at, published) VALUES (?,?,?,?,1)",
                 (g, "workbook 9B", old, old)).lastrowid
db.commit()
d, c = core.deadline_parts(old, cfg)
post("/assignments/%d/edit" % aid, {"title": "workbook 9B and 9C", "due": d, "due_time": c})
row = db.execute("SELECT title, due_at FROM assignments WHERE id=?", (aid,)).fetchone()
check("its title changes, its deadline stays", row["title"] == "workbook 9B and 9C" and row["due_at"] == old)
post("/assignments/%d/edit" % aid, {"title": "workbook 9B and 9C", "due": day(-2), "due_time": "12:00"})
check("but it cannot be moved to another past day",
      db.execute("SELECT due_at FROM assignments WHERE id=?", (aid,)).fetchone()["due_at"] == old)

print("\n4. SETTING THE SAME HOMEWORK AGAIN")
before = count()
url, pg = post("/groups/%d/repeat" % g, {"due": day(-3), "due_time": "23:59"})
check("with a past deadline sets nothing", count() == before and "That deadline has already passed" in pg)

print("\n5. A CLASS MOVES UP A LEVEL")
cls = get("/groups/%d" % g)
check("the class page can change its level", 'action="/groups/%d/level"' % g in cls and "Change level" in cls)
check("students see their level's handouts", "Unit 12A & 12C" in get("/s/%s?tab=handouts" % tok))
url, pg = post("/groups/%d/level" % g, {"level_id": pre})
check("it moves", db.execute("SELECT level_id FROM groups WHERE id=?", (g,)).fetchone()["level_id"] == pre)
check("the page says what that means", "216 is now Pre-Intermediate" in pg)
hand = get("/s/%s?tab=handouts" % tok)
check("and students see the new level's handouts, not the old",
      "Unit 1A & 1C" in hand and "Unit 12A & 12C" not in hand)
check("their homework stays", count() == before)

srv.shutdown()
print()
print("deadline_guard: %d checks, %d failed" % (checks, len(fails)))
sys.exit(1 if fails else 0)
