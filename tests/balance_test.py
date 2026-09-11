"""Balance — see the assertions for what it guarantees.

Run me with:  python3 run_tests.py            (all of them)
              python3 tests/balance_test.py   (just this one)
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
FIXTURES = os.path.join(ROOT, "tests", "fixtures")

import tempfile, shutil
from datetime import timedelta
tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None)

import core
core.init_db(); db = core.connect(); cfg = core.load_config()
g = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('T','TT',?)",
               (core.iso(core.now()),)).lastrowid
# a season of 15 lessons, the last one two days ago
start = core.now() - timedelta(days=32)
core.start_season(db, start)
sid = db.execute("INSERT INTO students (name, group_id, active, token, created_at)"
    " VALUES ('Ali',?,1,'tok0000000000000000',?)", (g, core.iso(core.now()))).lastrowid

lesson_days = []
for i in range(15):
    d = start + timedelta(days=i * 2)          # a lesson every other day
    lesson_days.append(d)
    db.execute("INSERT INTO lesson_marks (student_id, day, punctuality, behaviour,"
               " participation, created_at) VALUES (?,?,4,4,4,?)",
               (sid, core.local_day(d, cfg), core.iso(core.now())))
# homework set at every lesson, due two days later
tasks = []
for i, d in enumerate(lesson_days):
    tasks.append(db.execute(
        "INSERT INTO assignments (group_id, title, created_at, published, due_at)"
        " VALUES (?,?,?,1,?)",
        (g, "HW %d" % (i + 1), core.iso(d), core.iso(d + timedelta(days=2)))).lastrowid)
# handed in every one on time, all 8s, EXCEPT the last two which were skipped
for i, a in enumerate(tasks):
    if i >= 13:
        continue
    due = db.execute("SELECT due_at FROM assignments WHERE id=?", (a,)).fetchone()["due_at"]
    db.execute("INSERT INTO submissions (student_id, assignment_id, status, score,"
               " created_at, kind) VALUES (?,?,'graded',8,?,'photo')",
               (sid, a, core.iso(core.parse(due) - timedelta(hours=3))))
db.commit()

st = core.championship(db)
r = next(x for x in st["rows"] if x["student"]["id"] == sid)
hi, lessons, closed = core.season_window(db, sid, core.season_start(db), cfg)
print("15 lessons, homework set at each one, due two days after the lesson.")
print("The student skipped the last two.\n")
print("  lessons counted     :", r["lessons"], "of", core.SEASON_LESSONS)
print("  season closed on    :", closed)
print("  window shuts        :", core.local_day(core.parse(hi), cfg))
print("  HW 14 due           :", core.local_day(core.parse(
    db.execute("SELECT due_at FROM assignments WHERE id=?", (tasks[13],)).fetchone()["due_at"]), cfg))
print("  HW 15 due           :", core.local_day(core.parse(
    db.execute("SELECT due_at FROM assignments WHERE id=?", (tasks[14],)).fetchone()["due_at"]), cfg))
print()
print("  homework line       :", r["handed"])
print("  pieces counted      :", r["graded"], "of the 15 that were set")
print("  homework points     :", r["points"]["homework"], "of 3")
print("  final?              :", r["final"])

print("\nChecks:")
print("  the last two count as missed:", r["not_handed"] == 2)
assert r["not_handed"] == 2, r["not_handed"]
print("  all 15 are in the average  :", r["graded"] == 15)
assert r["graded"] == 15
avg = (13 * 8 + 0 + 0) / 15.0
print("  average is (13x8 + 0 + 0)/15 = %.2f/10 -> %.2f of 3" % (avg, avg / 10 * 3))
assert abs(r["points"]["homework"] - round(avg / 10 * 3, 2)) < 0.02

print("\nAnd a piece not yet due is left out, not counted as missed:")
d = lesson_days[-1]
db.execute("INSERT INTO assignments (group_id, title, created_at, published, due_at)"
           " VALUES (?,?,?,1,?)",
           (g, "HW 16", core.iso(d), core.iso(core.now() + timedelta(days=2))))
db.commit()
r2 = next(x for x in core.championship(db)["rows"] if x["student"]["id"] == sid)
print("  line                :", r2["handed"])
print("  still counted       :", r2["graded"], "| not due yet:", r2["pending"])
print("  points unchanged    :", r2["points"]["homework"] == r["points"]["homework"])
print("  now provisional     :", r2["final"] is False)
assert r2["pending"] == 1 and r2["graded"] == 15 and not r2["final"]
db.close(); shutil.rmtree(tmp)
print("\nConduct and homework now cover the same 15 lessons.")
