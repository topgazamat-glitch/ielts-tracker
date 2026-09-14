"""Grid grading — a whole task marked on one page, no load between students.

Run me with:  python3 run_tests.py gridgrade
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
core.init_db(); db = core.connect()
g = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('114','A',?)",
               (core.iso(core.now()),)).lastrowid
a1 = db.execute("INSERT INTO assignments (group_id, title, created_at, published, due_at)"
    " VALUES (?,'Essay 1',?,1,?)", (g, core.iso(core.now()),
    core.iso(core.now() + timedelta(days=1)))).lastrowid
a2 = db.execute("INSERT INTO assignments (group_id, title, created_at, published, due_at)"
    " VALUES (?,'Grammar p45',?,1,?)", (g, core.iso(core.now()),
    core.iso(core.now() + timedelta(days=1)))).lastrowid
subs = {}
for i, n in enumerate(("Ali", "Bek", "Dilnoza", "Malika")):
    sid = db.execute("INSERT INTO students (name, group_id, active, created_at)"
        " VALUES (?,?,1,?)", (n, g, core.iso(core.now()))).lastrowid
    for a in (a1, a2):
        s = db.execute("INSERT INTO submissions (student_id, assignment_id, created_at,"
            " kind) VALUES (?,?,?,'photo')", (sid, a, core.iso(core.now()))).lastrowid
        fn = "p%d_%d.jpg" % (a, sid)
        open(os.path.join(core.UPLOAD_DIR, fn), "wb").write(b"\xff\xd8\xff" + b"\0" * 500)
        db.execute("INSERT INTO files (submission_id, filename, ord) VALUES (?,?,0)", (s, fn))
        subs.setdefault(a, []).append((n, s))
db.commit(); db.close()

srv = server.Server(("127.0.0.1", 8872), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start(); time.sleep(0.4)
B = "http://127.0.0.1:8872"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(B + "/login", urllib.parse.urlencode({"password": "pw"}).encode()).read()
def get(u): return op.open(B + u).read().decode("utf-8")
def post(u, d): return op.open(B + u, urllib.parse.urlencode(d, doseq=True).encode()).read().decode("utf-8")

page = get("/queue/grid")
print("1. ONE TASK AT A TIME, EVERYONE TOGETHER")
cards = len(re.findall(r'class="gradecard"', page))
print("   cards on the page: %d (four students, one task)" % cards)
assert cards == 4
print("   each has the class's work shown:", page.count("/media/p%d_" % a1) == 4)
print("   tabs for each waiting task:", page.count('href="/queue/grid?assignment=') >= 2)
assert page.count('href="/queue/grid?assignment=') >= 2

print("\n2. THE OTHER TASK IS ITS OWN PAGE")
p2 = get("/queue/grid?assignment=%d" % a2)
print("   cards:", len(re.findall(r'class="gradecard"', p2)))
print("   shows the other task's work:", p2.count("/media/p%d_" % a2) == 4)
assert p2.count("/media/p%d_" % a2) == 4

print("\n3. MARK THREE, LEAVE ONE")
form = {"assignment": a1}
for (n, s), score in zip(subs[a1], (8, 7.5, 9)):
    form["score_%d" % s] = score
form["note_%d" % subs[a1][0][1]] = "good structure"
post("/grade/many", form)
db = core.connect()
done = db.execute("SELECT COUNT(*) c FROM submissions WHERE assignment_id=?"
                  " AND status='graded'", (a1,)).fetchone()["c"]
left = db.execute("SELECT COUNT(*) c FROM submissions WHERE assignment_id=?"
                  " AND status='pending'", (a1,)).fetchone()["c"]
print("   graded: %d | still waiting: %d" % (done, left))
assert done == 3 and left == 1
marks = [r["score"] for r in db.execute(
    "SELECT score FROM submissions WHERE assignment_id=? AND status='graded'"
    " ORDER BY score", (a1,))]
print("   marks stored, halves included:", marks)
assert marks == [7.5, 8.0, 9.0]
note = db.execute("SELECT note FROM submissions WHERE id=?", (subs[a1][0][1],)).fetchone()["note"]
print("   the note landed on the right student:", note)
assert note == "good structure"
db.close()

print("\n4. THE UNMARKED ONE IS STILL THERE TO DO")
page = get("/queue/grid?assignment=%d" % a1)
print("   cards remaining:", len(re.findall(r'class="gradecard"', page)))
assert len(re.findall(r'class="gradecard"', page)) == 1

print("\n5. THE ONE-AT-A-TIME QUEUE STILL WORKS")
q = get("/queue")
print("   queue page renders:", "Grading queue" in q)
print("   and links to the grid:", "/queue/grid" in q)
assert "Grading queue" in q and "/queue/grid" in q

print("\n6. THE PAGE STAYS SWAPPABLE")
body = re.search(r"<main[^>]*>(.*)</main>", get("/queue/grid"), re.S).group(1)
print("   no inline script in main:", "<script" not in body)
assert "<script" not in body
srv.shutdown(); shutil.rmtree(tmp)
print("\nA whole task marked on one page.")
