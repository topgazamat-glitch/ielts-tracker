"""In the league — a set of homework can be marked but not scored.

Run me with:  python3 run_tests.py inleague
"""
import http.cookiejar
import os
import re
import shutil
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
g = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('114','A',?)",
               (core.iso(core.now()),)).lastrowid
start = core.now() - timedelta(days=20)
core.start_season(db, start)
sid = db.execute("INSERT INTO students (name, group_id, active, created_at)"
                 " VALUES ('Ali',?,1,?)", (g, core.iso(core.now()))).lastrowid

dues = []
for k, marks in enumerate(([6, 6, 6], [9, 9, 9], [10, 10, 10])):
    made = start + timedelta(days=k)
    due = core.iso(made + timedelta(hours=12))
    dues.append(due)
    for i, m in enumerate(marks):
        a = db.execute("INSERT INTO assignments (group_id, title, created_at, published,"
            " due_at) VALUES (?,?,?,1,?)",
            (g, "set%d item%d" % (k, i), core.iso(made), due)).lastrowid
        db.execute("INSERT INTO submissions (student_id, assignment_id, status, score,"
                   " created_at, kind) VALUES (?,?,'graded',?,?,'photo')",
                   (sid, a, m, core.iso(core.parse(due) - timedelta(hours=1))))
db.commit()

def hw():
    r = next(x for x in core.championship(db)["rows"] if x["student"]["id"] == sid)
    return r["points"]["homework"], r["handed"]

print("1. THREE SETS COUNT")
pts, line = hw()
print("   %s  (%s)" % (pts, line))
print("   6s -> 1.8, 9s -> 2.7, 10s -> 3.0  = 7.5")
assert abs(pts - 7.5) < 0.01

print("\n2. LEAVE THE OLDEST ONE OUT")
core.set_in_league(db, g, dues[0], False)
pts, line = hw()
print("   %s  (%s)" % (pts, line))
print("   only 2.7 + 3.0 now")
assert abs(pts - 5.7) < 0.01
print("   the marks are still on record:",
      db.execute("SELECT COUNT(*) c FROM submissions WHERE student_id=?"
                 " AND status='graded'", (sid,)).fetchone()["c"], "graded pieces")
assert db.execute("SELECT COUNT(*) c FROM submissions WHERE student_id=?"
                  " AND status='graded'", (sid,)).fetchone()["c"] == 9

print("\n3. AND IT CAN BE PUT BACK")
core.set_in_league(db, g, dues[0], True)
pts, _ = hw()
print("   back to", pts)
assert abs(pts - 7.5) < 0.01
core.set_in_league(db, g, dues[0], False)
db.close()

print("\n4. THE SWITCH IS ON THE PAGE")
srv = server.Server(("127.0.0.1", 8873), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start(); time.sleep(0.4)
B = "http://127.0.0.1:8873"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(B + "/login", urllib.parse.urlencode({"password": "pw"}).encode()).read()
page = op.open(B + "/assignments?closed=1").read().decode("utf-8")
print("   excluded set is labelled:", "not in the league" in page)
print("   and offers to count it again:", "Count in the league" in page)
print("   the others offer to leave them out:", "Leave out of the league" in page)
assert "not in the league" in page and "Count in the league" in page

print("\n5. THE BUTTON WORKS")
op.open(B + "/assignments/batch/league",
        urllib.parse.urlencode({"group_id": g, "due": dues[0]}).encode()).read()
db = core.connect()
pts, _ = hw()
print("   after pressing it:", pts)
assert abs(pts - 7.5) < 0.01
db.close(); srv.shutdown(); shutil.rmtree(tmp)
print("\nA set of homework can be marked without scoring.")
