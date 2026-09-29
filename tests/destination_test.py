"""A Destination unit on the site: a line "Destination B1, Unit 12" in the
homework is that unit, done on the site or on paper like a handout - but it
opens only for the class it is set to, and never joins the chain of the
course's booklets.

Run me with:  python3 run_tests.py destination
"""
import json
import os
import sys
import tempfile
from datetime import timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None); os.environ["TEACHER_PASSWORD"] = "pw"
import core, server

db = core.init_db()
now = core.now()
fails, checks = [], 0


def check(what, cond):
    global checks
    checks += 1
    print(("  ok  " if cond else "  FAIL") + "  " + what)
    if not cond:
        fails.append(what)


pre = db.execute("SELECT id FROM levels WHERE name='Pre-Intermediate'").fetchone()["id"]
inter = db.execute("SELECT id FROM levels WHERE name='Intermediate'").fetchone()["id"]
g1 = db.execute("INSERT INTO groups (name, join_code, created_at, level_id) VALUES ('214','A',?,?)",
                (core.iso(now), pre)).lastrowid
g2 = db.execute("INSERT INTO groups (name, join_code, created_at, level_id) VALUES ('116','B',?,?)",
                (core.iso(now), inter)).lastrowid
ann = core.add_student(db, "Ann", g1)
ivy = core.add_student(db, "Ivy", g2)

print("1. THE UNIT, LOADED")
data = json.load(open(os.path.join(ROOT, "handouts", "dest_b1_12.json")))
d12 = core.load_test(db, data)
d23 = core.load_test(db, json.load(open(os.path.join(ROOT, "handouts", "dest_b1_23.json"))))
row = db.execute("SELECT * FROM dtests WHERE id=?", (d12,)).fetchone()
check("it is a handout of the Destination series", row["kind"] == "handout" and row["series"] == "destination")
check("with its answers", db.execute("SELECT COUNT(*) FROM dquestions WHERE test_id=? AND answer IS NOT NULL",
                                     (d12,)).fetchone()[0] == 81)
check("in four parts", len(server.handout_parts(row["layout"])[1]) == 4)
check("unit 23 in three", len(server.handout_parts(
    db.execute("SELECT layout FROM dtests WHERE id=?", (d23,)).fetchone()["layout"])[1]) == 3)
# a course booklet beside it, to see the two kept apart
course = core.load_test(db, {"level": "Pre-Intermediate", "number": 13, "title": "Unit 13A & 13C — Later",
                             "kind": "handout", "layout": data["layout"], "passages": {},
                             "questions": data["questions"]})
db.execute("UPDATE dtests SET published=1 WHERE id=?", (course,))
db.commit()

print("\n2. A LINE OF HOMEWORK NAMES IT")
for text, want in [("Destination B1, Unit 12", d12), ("destination b1 unit 12 (vocabulary)", d12),
                   ("Destination B1 · Unit 23 — Questions", d23), ("Destination B2, Unit 12", None),
                   ("Destination B1, Unit 5", None), ("Workbook unit 12", None)]:
    check("%r -> %s" % (text, "that unit" if want else "nothing"), core.destination_test(db, text) == want)

print("\n3. SET AS HOMEWORK")
st = lambda sid: db.execute("SELECT * FROM students WHERE id=?", (sid,)).fetchone()
check("before it is set, no class sees it", not any(b["id"] == d12 for b, _f in core.handout_shelf(db, st(ann))))
import threading, time, urllib.request, urllib.parse, http.cookiejar
srv = server.Server(("127.0.0.1", 8896), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
time.sleep(0.4)
base = "http://127.0.0.1:8896"
jar = http.cookiejar.CookieJar()
teacher = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
teacher.open(base + "/login", urllib.parse.urlencode({"password": "pw"}).encode()).read()
due = core.local_day(now + timedelta(days=3), core.load_config())
for gid in (g1, g2):
    teacher.open(base + "/assignments/list", urllib.parse.urlencode({
        "group_id": gid, "due": due, "due_time": "20:00", "publish": "1",
        "items": "Workbook unit 12 A&C\nDestination B1, Unit 12"}).encode(), timeout=30).read()
a = db.execute("SELECT * FROM assignments WHERE group_id=? AND title LIKE 'Destination%'", (g1,)).fetchone()
check("the Destination line is linked to the unit", a["test_id"] == d12)
check("the workbook line is not", db.execute(
    "SELECT test_id FROM assignments WHERE group_id=? AND title LIKE 'Workbook%'", (g1,)).fetchone()[0] is None)
shelf = core.handout_shelf(db, st(ann))
check("the class sees it among its booklets", any(b["id"] == d12 for b, _f in shelf))
check("and it is never shut behind a booklet", all(f is None for b, f in shelf if b["id"] == d12))
check("an Intermediate class it is set to sees it too", any(b["id"] == d12 for b, _f in core.handout_shelf(db, st(ivy))))
check("unit 23, not set, stays out of sight", not any(b["id"] == d23 for b, _f in shelf))
check("it opens for the class", core.handout_open_to(db, d12, g1) and not core.handout_open_to(db, d23, g1))

print("\n4. IT NEVER HOLDS UP A BOOKLET")
check("the course booklet after it is open though the unit is not done",
      core.handout_blocked_by(db, course, st(ann)) is None)
check("and the Set homework list of course handouts leaves it out",
      "Destination B1 · Unit 12" not in teacher.open(base + "/assignments", timeout=30).read().decode())

print("\n5. ON PAPER TOO")
sub = db.execute("INSERT INTO submissions (student_id, assignment_id, created_at, status, draft, kind)"
                 " VALUES (?,?,?,'pending',0,'photo')", (ann, a["id"], core.iso(now))).lastrowid
db.commit()
gp = teacher.open(base + "/queue?id=%d" % sub, timeout=30).read().decode()
check("its photos get the tick on the Grade screen", 'name="tick" value="done"' in gp)
teacher.open(base + "/grade", urllib.parse.urlencode({"submission_id": sub, "tick": "done"}).encode(),
             timeout=30).read()
hw = core.handout_homework(db, db.execute("SELECT * FROM assignments WHERE id=?", (a["id"],)).fetchone(), ann)
check("and count 5, on paper", hw["mark"] == 5 and hw["route"] == "paper")
plan = json.loads(teacher.open(base + "/assignments/unit.json?" + urllib.parse.urlencode(
    {"group_id": g1, "unit": 12, "pair": "A&C", "kind": "none",
     "destination": "Destination B1, Unit 12"}), timeout=30).read())
check("the Set homework form knows the Destination unit is on the site",
      any(i["kind"] == "destination" and i["test_id"] == d12 for i in plan["items"]))

print("\n6. THE TEACHER CAN FIND IT")
tp = teacher.open(base + "/tests", timeout=30).read().decode()
check("the Tests page lists the Destination units first, with where each is set",
      tp.find("Destination B1 · Unit 12") < tp.find("Unit 13A") and "set to 116, 214" in tp
      and "/tests/%d/look" % d23 in tp and "not set yet" in tp)
look = teacher.open(base + "/tests/%d/look?part=2" % d12, timeout=30).read().decode()
check("its look-through page shows a part as a student sees it",
      "Part 2 of 4" in look and "Choose the correct word" in look and "bk-chip" in look)
with_key = teacher.open(base + "/tests/%d/look?part=1&answers=1" % d12, timeout=30).read().decode()
check("and, asked, with the key's answers in the boxes", 'value="grateful"' in with_key)
sh = teacher.open(base + "/assignments", timeout=30).read().decode()
check("Set homework offers the units on the site, to type or to tap",
      '<datalist id="destlist">' in sh and 'data-dest="Destination B1, Unit 12"' in sh
      and 'data-dest="Destination B1, Unit 23"' in sh)

print("\n7. A WORKBOOK UNIT IS LINKED FROM ITS LINE")
wbu = core.load_test(db, json.load(open(os.path.join(ROOT, "handouts", "wb_pi_01ac.json"))))
check("it is a workbook handout", db.execute("SELECT series FROM dtests WHERE id=?", (wbu,)).fetchone()[0] == "workbook")
for text, level, want in [("Workbook unit 1 A&C", pre, wbu), ("workbook unit 1 A & C", pre, wbu),
                          ("Workbook unit 1 B&D", pre, None), ("Workbook unit 1 A&C", inter, None),
                          ("Workbook unit 2 A&C", pre, None)]:
    check("%r at level %d -> %s" % (text, level, "the unit" if want else "nothing"),
          core.workbook_test(db, text, level) == want)
teacher.open(base + "/assignments/list", urllib.parse.urlencode({
    "group_id": g1, "due": due, "due_time": "21:00", "publish": "1",
    "items": "Workbook unit 1 A&C"}).encode(), timeout=30).read()
check("setting the line links it", db.execute(
    "SELECT test_id FROM assignments WHERE group_id=? AND title='Workbook unit 1 A&C' AND due_at LIKE '%T16:00%'",
    (g1,)).fetchone()[0] == wbu)
plan = json.loads(teacher.open(base + "/assignments/unit.json?" + urllib.parse.urlencode(
    {"group_id": g1, "unit": 1, "pair": "A&C", "kind": "none"}), timeout=30).read())
check("the Set homework form knows the workbook unit is on the site",
      plan["items"][0]["kind"] == "workbook" and plan["items"][0]["test_id"] == wbu)
check("the Tests page has a Workbook section with it", "Workbook · Unit 1A &amp; 1C" in
      teacher.open(base + "/tests", timeout=30).read().decode())
srv.shutdown()

print()
print("destination: %d checks, %d failed" % (checks, len(fails)))
sys.exit(1 if fails else 0)
