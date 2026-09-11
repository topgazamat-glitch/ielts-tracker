"""Scope — see the assertions for what it guarantees.

Run me with:  python3 run_tests.py            (all of them)
              python3 tests/scope_test.py   (just this one)
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
FIXTURES = os.path.join(ROOT, "tests", "fixtures")

import tempfile, shutil, threading, time, re, random, http.cookiejar
import urllib.request, urllib.parse
from datetime import timedelta
tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None); os.environ["TEACHER_PASSWORD"] = "testpw123"

import core, server
core.init_db(); db = core.connect(); cfg = core.load_config()
random.seed(11)
gids = []
for i, nm in enumerate(["Beginner", "Elementary", "Intermediate"]):
    gids.append(db.execute("INSERT INTO groups (name, join_code, created_at)"
                " VALUES (?,?,?)", (nm, "S%02d" % i, core.iso(core.now()))).lastrowid)
start = core.now() - timedelta(days=20)
core.start_season(db, start)
weak = None
for i in range(24):
    g = gids[i % 3]
    sid = db.execute("INSERT INTO students (name, group_id, active, token, created_at)"
          " VALUES (?,?,1,?,?)", ("Student %02d" % i, g, "tok%016d" % i,
          core.iso(core.now()))).lastrowid
    if i == 0: weak = sid
    # Beginner students score lower, so a school-wide table buries them
    base = 4 if g == gids[0] else 8
    for k in range(4):
        made = start + timedelta(days=k)
        a = db.execute("INSERT INTO assignments (group_id, title, created_at, published,"
            " due_at) VALUES (?,?,?,1,?)",
            (g, "Task %d.%d" % (i, k), core.iso(made),
             core.iso(made + timedelta(days=1)))).lastrowid
        db.execute("INSERT INTO submissions (student_id, assignment_id, status, score,"
                   " created_at, kind) VALUES (?,?,'graded',?,?,'photo')",
                   (sid, a, base + random.choice([0, 1]),
                    core.iso(made + timedelta(hours=6))))
    for d in range(6):
        db.execute("INSERT INTO lesson_marks (student_id, day, punctuality, behaviour,"
                   " participation, created_at) VALUES (?,?,4,4,4,?)",
                   (sid, core.local_day(start + timedelta(days=d), cfg), core.iso(core.now())))
db.commit()

full = core.championship(db)
beg = core.scope_standing(full, gids[0])
print("1. SCOPING")
w = next(r for r in full["rows"] if r["student"]["id"] == weak)
w2 = next(r for r in beg["rows"] if r["student"]["id"] == weak)
print("   %s: %d%s of %d in the school, but %d%s of %d in their class" % (
    w["student"]["name"], w["rank"] or 0, "", len(full["rows"]),
    w2["rank"] or 0, "", len(beg["rows"])))
assert w2["rank"] < w["rank"], "class rank must be better than school rank"
assert w["total"] == w2["total"], "the score itself must not change"
print("   the score is identical, only the neighbours change:", w["total"])
db.close()

srv = server.Server(("127.0.0.1", 8812), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start(); time.sleep(0.4)
B = "http://127.0.0.1:8812"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(B + "/login", urllib.parse.urlencode({"password": "testpw123"}).encode()).read()
def get(u, o=None): return (o or op).open(B + u).read().decode("utf-8")

print("\n2. STUDENT PAGE - one table now, not two")
pg = get("/s/tok0000000000000000?tab=class", urllib.request.build_opener())
print("   'Class standings' table gone:", "Class standings" not in pg)
print("   championship present:       ", "Championship" in pg)
print("   class/school toggle:        ", "scope=school" in pg and "scope=class" in pg)
print("   their own homework line:    ", "Your homework" in pg)
assert "Class standings" not in pg and "scope=school" in pg
tables = pg.count("<table")
print("   tables on the page:", tables, "(was 2)")
assert tables == 1, tables

print("\n3. THE TOGGLE WORKS")
cls = get("/s/tok0000000000000000?tab=class&scope=class", urllib.request.build_opener())
sch = get("/s/tok0000000000000000?tab=class&scope=school", urllib.request.build_opener())
nc = len(re.findall(r"<tr", cls)); ns = len(re.findall(r"<tr", sch))
print("   my class: %d rows | whole school: %d rows" % (nc, ns))
assert ns > nc
print("   class view says 'in your class':", "in your class" in cls)
print("   school view says 'in the school':", "in the school" in sch)
print("   prize is still described as school-wide:",
      "best in the whole school" in cls)
assert "in your class" in cls and "in the school" in sch

print("\n4. TEACHER LEAGUE - class filter")
t = get("/championship")
tc = get("/championship?class=%d" % gids[0])
print("   class tabs present:", "/championship?class=" in t)
print("   whole school rows: %d | one class: %d" % (t.count("<tr"), tc.count("<tr")))
assert tc.count("<tr") < t.count("<tr")
print("   Group column dropped when filtered:", "<th>Group</th>" not in tc)

print("\n5. PROGRESS PAGE - teacher diagnostic")
r = get("/ratings")
print("   renamed:", "<h1>Progress</h1>" in r)
print("   nav label:", ">Progress<" in r)
print("   explains the split:", "cannot tell you who has stopped" in r)
print("   attention block:", "Nobody is behind" in r or "Not handing work in" in r)
assert "<h1>Progress</h1>" in r and ">Progress<" in r
srv.shutdown(); shutil.rmtree(tmp)
print("\nAll three changes verified.")
