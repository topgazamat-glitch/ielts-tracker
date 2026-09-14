"""Accumulating — more good work means more points, not the same points.

Run me with:  python3 run_tests.py accumulate
"""
import os
import shutil
import sys
import tempfile
from datetime import timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None)
import core
core.init_db(); db = core.connect(); cfg = core.load_config()
g = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('T','T',?)",
               (core.iso(core.now()),)).lastrowid
start = core.now() - timedelta(days=40)
core.start_season(db, start)

def student(n):
    return db.execute("INSERT INTO students (name, group_id, active, created_at)"
        " VALUES (?,?,1,?)", (n, g, core.iso(core.now()))).lastrowid

tasks = []
for i in range(core.SEASON_LESSONS):
    made = start + timedelta(days=i)
    tasks.append(db.execute(
        "INSERT INTO assignments (group_id, title, created_at, published, due_at)"
        " VALUES (?,?,?,1,?)", (g, "HW %d" % i, core.iso(made),
        core.iso(made + timedelta(hours=12)))).lastrowid)

def hand(sid, i, score):
    due = db.execute("SELECT due_at FROM assignments WHERE id=?", (tasks[i],)).fetchone()["due_at"]
    db.execute("INSERT INTO submissions (student_id, assignment_id, status, score,"
               " created_at, kind) VALUES (?,?,'graded',?,?,'photo')",
               (sid, tasks[i], score, core.iso(core.parse(due) - timedelta(hours=1))))

def lessons(sid, n, mark=5):
    for i in range(n):
        core.save_mark(db, sid, core.local_day(start + timedelta(days=i), cfg),
                       {"punctuality": mark, "behaviour": mark, "participation": mark}, None)

print("1. WORDS NO LONGER SCORE")
print("   components:", [(k, w) for k, _l, w in core.CHAMPIONSHIP])
print("   worth per fixture: homework %g, lesson %g"
      % (core.HOMEWORK_PER_SET, core.CONDUCT_PER_LESSON))
assert [k for k, _l, _w in core.CHAMPIONSHIP] == ["homework", "conduct"]
assert core.CHAMPIONSHIP_MAX == 5.0

print("\n2. MORE LESSONS, MORE POINTS")
for n in (1, 2, 5, 15):
    sid = student("Lessons %d" % n)
    lessons(sid, n)
db.commit()
rows = {r["student"]["name"]: r for r in core.championship(db)["rows"]}
last = -1
for n in (1, 2, 5, 15):
    r = rows["Lessons %d" % n]
    print("   %-2d lesson(s) at 5/5/5 -> in the lesson %s" % (n, r["points"]["conduct"]))
    assert r["points"]["conduct"] > last
    last = r["points"]["conduct"]
# a lesson at five out of five is two points, every time
print("   fifteen lessons at 5/5/5 -> %s  (15 x 2)" % rows["Lessons 15"]["points"]["conduct"])
assert rows["Lessons 15"]["points"]["conduct"] == 30.0
assert rows["Lessons 1"]["points"]["conduct"] == 2.0

print("\n3. MORE HOMEWORK, MORE POINTS")
for n in (1, 3, 8, 15):
    sid = student("HW %d" % n)
    lessons(sid, 3)
    for i in range(n):
        hand(sid, i, 10)
db.commit()
rows = {r["student"]["name"]: r for r in core.championship(db)["rows"]}
last = -1
for n in (1, 3, 8, 15):
    r = rows["HW %d" % n]
    print("   %-2d piece(s) at 10/10 -> homework %s" % (n, r["points"]["homework"]))
    assert r["points"]["homework"] > last
    last = r["points"]["homework"]
# each piece was set on its own day, so each is a fixture worth 3
print("   fifteen pieces at 10 -> %s  (15 x 3)" % rows["HW 15"]["points"]["homework"])
assert rows["HW 15"]["points"]["homework"] == 45.0
assert rows["HW 1"]["points"]["homework"] == 3.0

print("\n4. QUALITY STILL MATTERS")
good = student("All tens"); lessons(good, 3)
ok = student("All sixes"); lessons(ok, 3)
for i in range(10):
    hand(good, i, 10)
    hand(ok, i, 6)
db.commit()
rows = {r["student"]["name"]: r for r in core.championship(db)["rows"]}
print("   ten pieces at 10 -> %s | ten pieces at 6 -> %s"
      % (rows["All tens"]["points"]["homework"], rows["All sixes"]["points"]["homework"]))
assert rows["All tens"]["points"]["homework"] > rows["All sixes"]["points"]["homework"]

print("\n5. THE TOTAL IS THE TWO ADDED TOGETHER, WITH NO CEILING")
extra = student("Overachiever"); lessons(extra, 3)
for i in range(core.SEASON_LESSONS):
    hand(extra, i, 10)
db.commit()
r = {x["student"]["name"]: x for x in core.championship(db)["rows"]}["Overachiever"]
print("   fifteen tens and three lessons -> homework %s, in the lesson %s, total %s"
      % (r["points"]["homework"], r["points"]["conduct"], r["total"]))
assert r["points"]["homework"] == 45.0
assert r["total"] == round(r["points"]["homework"] + r["points"]["conduct"], 2)
db.close(); shutil.rmtree(tmp)
print("\nPoints add up now.")
