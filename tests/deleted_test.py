"""Deleted — see the assertions for what it guarantees.

Run me with:  python3 run_tests.py            (all of them)
              python3 tests/deleted_test.py   (just this one)
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

import core, server
core.init_db(); db = core.connect(); cfg = core.load_config()
g = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('114','A',?)",
               (core.iso(core.now()),)).lastrowid
start = core.now() - timedelta(days=20)
core.start_season(db, start)
sid = db.execute("INSERT INTO students (name, group_id, active, token, created_at)"
    " VALUES ('Ali',?,1,'tok0000000000000000',?)", (g, core.iso(core.now()))).lastrowid

def task(title, days_ago, due_in=2, published=1):
    made = start + timedelta(days=days_ago)
    return db.execute("INSERT INTO assignments (group_id, title, created_at, published,"
        " due_at) VALUES (?,?,?,?,?)",
        (g, title, core.iso(made), published,
         core.iso(made + timedelta(days=due_in)))).lastrowid

def hand(a, score):
    due = db.execute("SELECT due_at FROM assignments WHERE id=?", (a,)).fetchone()["due_at"]
    db.execute("INSERT INTO submissions (student_id, assignment_id, status, score,"
               " created_at, kind) VALUES (?,?,'graded',?,?,'photo')",
               (sid, a, score, core.iso(core.parse(due) - timedelta(hours=2))))

old1, old2, old3 = task("Old 1", 1), task("Old 2", 3), task("Old 3", 5)
for a in (old1, old2, old3):
    hand(a, 10)                      # marked 10/10 on all the old work
keep = task("This week", 12)
hand(keep, 6)                        # a 6 on the homework that still exists
db.commit()

r = next(x for x in core.championship(db)["rows"] if x["student"]["id"] == sid)
print("Before deleting anything:")
print("   %-38s hw %s of 3" % (r["handed"], r["points"]["homework"]))
assert r["graded"] == 4

print("\nNow delete the three old tasks, the way the site does it")
srv = server.Server(("127.0.0.1", 8850), server.Handler)
import threading, time, urllib.request, urllib.parse, http.cookiejar
os.environ["TEACHER_PASSWORD"] = "pw"; server.CFG = core.load_config()
db.close()
threading.Thread(target=srv.serve_forever, daemon=True).start(); time.sleep(0.4)
B = "http://127.0.0.1:8850"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(B + "/login", urllib.parse.urlencode({"password": "pw"}).encode()).read()
for a in (old1, old2, old3):
    op.open(B + "/assignments/%d/delete" % a, b"").read()

db = core.connect()
left = db.execute("SELECT COUNT(*) c FROM assignments").fetchone()["c"]
subs = db.execute("SELECT COUNT(*) c FROM submissions WHERE student_id=?", (sid,)).fetchone()["c"]
orphan = db.execute("SELECT COUNT(*) c FROM submissions WHERE student_id=?"
                    " AND assignment_id IS NULL", (sid,)).fetchone()["c"]
print("   assignments left: %d | the student's marked work still on record: %d"
      " (%d now loose)" % (left, subs, orphan))
assert left == 1 and subs == 4 and orphan == 3

r = next(x for x in core.championship(db)["rows"] if x["student"]["id"] == sid)
print("\nAfter deleting:")
print("   %-38s hw %s of 3" % (r["handed"], r["points"]["homework"]))
print("   counted pieces:", r["graded"], "(only the homework that still exists)")
assert r["graded"] == 1
assert abs(r["points"]["homework"] - 1.8) < 0.01, r["points"]["homework"]
print("   the three 10s from deleted tasks no longer score:", r["points"]["homework"], "= 6/10 -> 1.8")

print("\nThe student's own record is untouched:")
sp = urllib.request.urlopen(B + "/s/tok0000000000000000?tab=progress").read().decode()
print("   their page still shows their marks:", sp.count("10") > 0 or "6" in sp)
db.close(); srv.shutdown(); shutil.rmtree(tmp)
print("\nDeleted homework stops scoring; existing homework keeps scoring.")
