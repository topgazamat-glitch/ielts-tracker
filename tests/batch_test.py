"""Batch — see the assertions for what it guarantees.

Run me with:  python3 run_tests.py            (all of them)
              python3 tests/batch_test.py   (just this one)
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
FIXTURES = os.path.join(ROOT, "tests", "fixtures")

import tempfile, shutil, threading, time, re, http.cookiejar
import urllib.request, urllib.parse
tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None); os.environ["TEACHER_PASSWORD"] = "testpw123"

import core, server
core.init_db(); db = core.connect(); cfg = core.load_config()
g = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('Inter','TT',?)",
               (core.iso(core.now()),)).lastrowid
sids = [db.execute("INSERT INTO students (name, group_id, active, token, created_at)"
        " VALUES (?,?,1,?,?)", ("S%d" % i, g, "tok%016d" % i,
        core.iso(core.now()))).lastrowid for i in range(4)]
db.commit(); db.close()
srv = server.Server(("127.0.0.1", 8814), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start(); time.sleep(0.4)
B = "http://127.0.0.1:8814"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(B + "/login", urllib.parse.urlencode({"password": "testpw123"}).encode()).read()
def get(u): return op.open(B + u).read().decode("utf-8")
def post(u, d): return op.open(B + u, urllib.parse.urlencode(d, doseq=True).encode()).read().decode("utf-8")

post("/assignments/list", {"group_id": g, "items": "Essay\nGrammar p45\nReading 2",
     "task_type": "task2", "due": "2026-09-20", "due_time": "18:00", "publish": "1"})
post("/assignments/list", {"group_id": g, "items": "Listening 3",
     "task_type": "other", "due": "2026-09-27", "due_time": "20:00", "publish": "1"})
db = core.connect()
first = db.execute("SELECT due_at FROM assignments WHERE title='Essay'").fetchone()["due_at"]
# two students hand in, one gets marked
a = db.execute("SELECT id FROM assignments WHERE title='Essay'").fetchone()["id"]
db.execute("INSERT INTO submissions (student_id, assignment_id, status, score, created_at,"
           " kind) VALUES (?,?,'graded',8,?,'photo')", (sids[0], a, core.iso(core.now())))
db.execute("INSERT INTO submissions (student_id, assignment_id, created_at, kind)"
           " VALUES (?,?,?,'photo')", (sids[1], a, core.iso(core.now())))
db.commit(); db.close()

pg = get("/assignments")
print("1. GROUPED AS YOU SET THEM")
n = pg.count('class="card batch"')
print("   batches shown:", n, "(two postings)")
assert n == 2, n
print("   items counted:", "3 item(s)" in pg and "1 item(s)" in pg)
print("   who has sent:", "2 of 4 students" in pg)
print("   marked count warned:", "1 marked" in pg)
assert "3 item(s)" in pg and "2 of 4 students" in pg

print("\n2. BATCH BUTTONS PRESENT")
for act in ("close", "delete", "edit"):
    print("   %-7s ->" % act, "/assignments/batch/%s" % act in pg)
    assert "/assignments/batch/%s" % act in pg
print("   per-item close/delete still there:",
      "/close" in pg and "/delete" in pg)

print("\n3. MOVE THE WHOLE DEADLINE")
post("/assignments/batch/edit", {"group_id": g, "due": first,
     "new_due": "2026-09-30", "new_time": "12:00"})
db = core.connect()
rows = db.execute("SELECT title, due_at FROM assignments ORDER BY id").fetchall()
for r in rows[:3]:
    d, t = core.deadline_parts(r["due_at"], cfg)
    print("   %-12s -> %s %s" % (r["title"], d, t))
    assert (d, t) == ("2026-09-30", "12:00")
print("   the other batch untouched:",
      core.deadline_parts(rows[3]["due_at"], cfg))
assert core.deadline_parts(rows[3]["due_at"], cfg) == ("2026-09-27", "20:00")
moved = rows[0]["due_at"]
db.close()

print("\n4. CLOSE AND REOPEN THE BATCH")
post("/assignments/batch/close", {"group_id": g, "due": moved})
db = core.connect()
print("   closed:", [r["closed"] for r in db.execute(
    "SELECT closed FROM assignments WHERE due_at=?", (moved,))])
assert all(r["closed"] == 1 for r in db.execute(
    "SELECT closed FROM assignments WHERE due_at=?", (moved,)))
db.close()
print("   hidden by default:", "Essay" not in get("/assignments"))
print("   visible with show closed:", "Essay" in get("/assignments?closed=1"))
post("/assignments/batch/open", {"group_id": g, "due": moved})
db = core.connect()
assert all(r["closed"] == 0 for r in db.execute(
    "SELECT closed FROM assignments WHERE due_at=?", (moved,)))
print("   reopened: True")
db.close()

print("\n5. DELETE KEEPS THE STUDENT'S MARK")
post("/assignments/batch/delete", {"group_id": g, "due": moved})
db = core.connect()
left = db.execute("SELECT COUNT(*) c FROM assignments").fetchone()["c"]
sub = db.execute("SELECT score, status, assignment_id FROM submissions"
                 " WHERE student_id=?", (sids[0],)).fetchone()
print("   assignments left:", left, "(only the other batch)")
print("   the marked 8/10 survives:", sub["score"], sub["status"],
      "| unlinked:", sub["assignment_id"] is None)
assert left == 1 and sub["score"] == 8 and sub["assignment_id"] is None
db.close()

print("\n6. PAGE STILL SWAPPABLE")
pg = get("/assignments")
print("   no inline script in main:",
      "<script" not in re.search(r"<main[^>]*>(.*)</main>", pg, re.S).group(1))
srv.shutdown(); shutil.rmtree(tmp)
print("\nBatch management works.")
