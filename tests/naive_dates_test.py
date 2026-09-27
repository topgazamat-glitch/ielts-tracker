"""A bare date in the database must not take a page down — see the assertions.

Run me with:  python3 run_tests.py                 (all of them)
              python3 tests/naive_dates_test.py   (just this one)
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import tempfile, shutil
tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None)

import core
core.init_db(); db = core.connect()
now = core.iso(core.now())
g = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('110','AA',?)", (now,)).lastrowid
sid = db.execute("INSERT INTO students (name, group_id, active, token, created_at)"
                 " VALUES ('Laylo',?,1,'tok0000000000000001',?)", (g, now)).lastrowid
a = db.execute("INSERT INTO assignments (group_id, title, created_at, published, due_at)"
               " VALUES (?,?,?,1,?)", (g, "Workbook", now, now)).lastrowid
db.execute("INSERT INTO submissions (student_id, assignment_id, created_at, status, kind)"
           " VALUES (?,?,?,'graded','photo')", (sid, a, now))
db.commit()

print("1. PARSE ALWAYS GIVES AN INSTANT")
for ts in ("2026-09-27", "2026-09-27T10:00:00", "2026-09-27 10:00:00", "2026-09-27T10:00:00+00:00"):
    d = core.parse(ts)
    print("   %-26s aware: %s" % (ts, d.tzinfo is not None))
    assert d.tzinfo is not None
print("   and subtracts from now() without complaint:", (core.now() - core.parse("2026-09-27")).days >= 0)

print("\n2. A LEAVER MARKED WITH A DAY, AS THE FORM SENDS IT")
core.mark_left(db, sid, "moved", when="2026-09-27")
e = db.execute("SELECT ended_at FROM enrolments WHERE student_id=?", (sid,)).fetchone()
print("   stored as an instant:", e["ended_at"])
assert e["ended_at"] == "2026-09-27T12:00:00+00:00"
pts = core.cycle_points(db, g)
print("   Insights still computes:", len(pts) == 1 and pts[0]["left"] and pts[0]["quiet_days"] is not None)
assert len(pts) == 1 and pts[0]["left"] and pts[0]["quiet_days"] is not None

print("\n3. AN OLD BARE-DATE ROW IS MENDED ON START-UP")
db.execute("UPDATE enrolments SET ended_at='2026-09-20' WHERE student_id=?", (sid,))
db.commit()
core.migrate(db)
e = db.execute("SELECT ended_at FROM enrolments WHERE student_id=?", (sid,)).fetchone()
print("   mended:", e["ended_at"])
assert e["ended_at"] == "2026-09-20T12:00:00+00:00"
print("   and the retention figure still counts them:", core.retention(db)["left"] == 1)
assert core.retention(db)["left"] == 1

db.close(); shutil.rmtree(tmp)
print("\nA date is a day; the database wants an instant; both are now fine.")
