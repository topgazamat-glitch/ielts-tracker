"""Pause — see the assertions for what it guarantees.

Run me with:  python3 run_tests.py            (all of them)
              python3 tests/pause_test.py   (just this one)
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
FIXTURES = os.path.join(ROOT, "tests", "fixtures")

import tempfile, shutil
tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp

import core, server
from datetime import timedelta
core.init_db(); db = core.connect(); cfg = core.load_config()

g = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('T','TT',?)",
               (core.iso(core.now()),)).lastrowid
def mk(n): return db.execute("INSERT INTO students (name, group_id, active, token,"
    " created_at) VALUES (?,?,1,?,?)", (n, g, n, core.iso(core.now()))).lastrowid
ali, vali = mk("Ali"), mk("Vali")
db.commit()

start = core.now() - timedelta(days=40)
core.start_season(db, start)
def task(n):
    made = start + timedelta(days=n)
    return db.execute("INSERT INTO assignments (group_id, title, created_at, published,"
        " due_at) VALUES (?,?,?,1,?)",
        (g, "HW %d" % n, core.iso(made), core.iso(made + timedelta(hours=12)))).lastrowid
tasks = {}
def hand(sid, day, score):
    # the homework exists because it was handed in - this test is about the
    # pause, not about work nobody did
    if day not in tasks:
        tasks[day] = task(day)
    db.execute("INSERT INTO submissions (student_id, assignment_id, status, score,"
               " created_at, kind) VALUES (?,?,'graded',?,?,'photo')",
               (sid, tasks[day], score, core.iso(start + timedelta(days=day, hours=1))))
def lesson(sid, day, v):
    db.execute("INSERT OR REPLACE INTO lesson_marks (student_id, day, punctuality,"
               " behaviour, participation, created_at) VALUES (?,?,?,?,?,?)",
               (sid, core.local_day(start + timedelta(days=day), cfg), v, v, v,
                core.iso(core.now())))

# Both work identically for the first 5 days
for d in (1, 2, 3):
    hand(ali, d, 6); hand(vali, d, 6)
for d in range(5):
    lesson(ali, d, 3); lesson(vali, d, 3)
db.commit()

before = {r["student"]["name"]: r for r in core.championship(db)["rows"]}
print("Before the pause")
for n, r in before.items():
    print("   %-5s total %-5s hw %-5s conduct %-5s lessons %d" % (
        n, r["total"], r["points"]["homework"], r["points"]["conduct"], r["lessons"]))

# --- pause on day 10, resume on day 20
core.pause_season(db, start + timedelta(days=10))
print("\nPaused on day 10. Ali keeps working through the pause, Vali does not.")
for d in (11, 13, 15, 17):
    hand(ali, d, 10)                       # perfect marks, during the pause
for d in range(10, 20):
    lesson(ali, d, 5)                      # perfect conduct, during the pause
db.commit()

st = core.championship(db)
during = {r["student"]["name"]: r for r in st["rows"]}
print("   paused flag on the table:", st["paused"])
for n, r in during.items():
    print("   %-5s total %-5s hw %-5s conduct %-5s lessons %d" % (
        n, r["total"], r["points"]["homework"], r["points"]["conduct"], r["lessons"]))
assert during["Ali"]["total"] == before["Ali"]["total"], "pause did not freeze the score"
assert during["Ali"]["lessons"] == before["Ali"]["lessons"], "lesson count moved while paused"
print("   -> Ali's four 10/10s and ten perfect lessons changed nothing. Frozen.")

core.resume_season(db, start + timedelta(days=20))
print("\nResumed on day 20. Ali works again.")
hand(ali, 21, 10); lesson(ali, 21, 5)
db.commit()
after = {r["student"]["name"]: r for r in core.championship(db)["rows"]}
for n, r in after.items():
    print("   %-5s total %-5s hw %-5s conduct %-5s lessons %d" % (
        n, r["total"], r["points"]["homework"], r["points"]["conduct"], r["lessons"]))
assert after["Ali"]["total"] > during["Ali"]["total"], "resume did not restart scoring"
assert after["Ali"]["graded"] == 4, ("3 before + 1 after, the 4 during are gone",
                                     after["Ali"]["graded"])
assert after["Ali"]["lessons"] == 6, ("5 before + 1 after", after["Ali"]["lessons"])
print("   -> counts 4 homeworks (3 before + 1 after) and 6 lessons (5 + 1).")
print("      The 4 pieces and 10 lessons from the pause stay excluded for good.")

print("\nA second pause stacks on the first")
core.pause_season(db, start + timedelta(days=25))
hand(ali, 26, 10); db.commit()
two = {r["student"]["name"]: r for r in core.championship(db)["rows"]}
assert two["Ali"]["graded"] == 4, two["Ali"]["graded"]
print("   windows:", core.pause_windows(db)[0][0][:10], "->",
      core.pause_windows(db)[0][1][:10], "and", core.pause_windows(db)[1][0][:10], "-> open")
core.resume_season(db, start + timedelta(days=27))

print("\nStarting a fresh season wipes the pause history")
core.start_season(db)
print("   pauses now:", core.pause_windows(db), "paused:", core.is_paused(db))
assert core.pause_windows(db) == [] and not core.is_paused(db)
print("\nAll pause checks passed.")
db.close(); shutil.rmtree(tmp)
