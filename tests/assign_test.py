"""Assign — see the assertions for what it guarantees.

Run me with:  python3 run_tests.py            (all of them)
              python3 tests/assign_test.py   (just this one)
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
core.init_db(); db = core.connect()
g = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('Inter','TT',?)",
               (core.iso(core.now()),)).lastrowid
db.execute("INSERT INTO students (name, group_id, active, token, created_at)"
           " VALUES ('Ali',?,1,'tok0000000000000000',?)", (g, core.iso(core.now())))
db.commit(); db.close()
srv = server.Server(("127.0.0.1", 8813), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start(); time.sleep(0.4)
B = "http://127.0.0.1:8813"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(B + "/login", urllib.parse.urlencode({"password": "testpw123"}).encode()).read()
def get(u): return op.open(B + u).read().decode("utf-8")
def post(u, d): return op.open(B + u, urllib.parse.urlencode(d, doseq=True).encode()).read().decode("utf-8")

pg = get("/assignments")
print("1. ONE FORM NOW")
print("   forms that create homework:", pg.count('action="/assignments/list"'))
print("   old single form gone:", '/assignments/new' not in pg)
assert pg.count('action="/assignments/list"') == 1 and "/assignments/new" not in pg
print("   it kept Type:      ", 'name="task_type"' in pg)
print("   it kept criteria:  ", 'name="rubric"' in pg)
print("   it kept due + time:", 'name="due"' in pg and 'name="due_time"' in pg)
assert 'name="task_type"' in pg and 'name="rubric"' in pg

print("\n2. ONE LINE MAKES ONE PIECE OF HOMEWORK")
post("/assignments/list", {"group_id": g, "items": "Task 2 essay - Technology",
     "task_type": "task2", "due": "2026-09-20", "due_time": "18:00",
     "publish": "1", "rubric": "1"})
db = core.connect()
rows = db.execute("SELECT * FROM assignments").fetchall()
print("   created:", [(r["title"], r["task_type"], r["rubric"], r["published"]) for r in rows])
assert len(rows) == 1
a = rows[0]
assert a["title"] == "Task 2 essay - Technology" and a["task_type"] == "task2"
assert a["rubric"] == 1 and a["published"] == 1
d, t = core.deadline_parts(a["due_at"], core.load_config())
print("   deadline kept the exact time:", d, t)
assert (d, t) == ("2026-09-20", "18:00")
db.close()

print("\n3. SEVERAL LINES STILL MAKE SEVERAL")
post("/assignments/list", {"group_id": g,
     "items": "Grammar page 45\nVocabulary unit 4\nReading passage 2",
     "task_type": "other", "due": "2026-09-25", "due_time": "23:59", "publish": "1"})
db = core.connect()
n = db.execute("SELECT COUNT(*) c FROM assignments").fetchone()["c"]
made = db.execute("SELECT title, rubric FROM assignments WHERE due_at LIKE '2026-09-25%'"
                  " OR due_at LIKE '2026-09-26%'").fetchall()
print("   total assignments now:", n, "| this batch:", [r["title"] for r in made])
assert n == 4 and len(made) == 3
print("   criteria off when unticked:", all(r["rubric"] == 0 for r in made))
db.close()

print("\n4. DRAFTS STILL WORK")
post("/assignments/list", {"group_id": g, "items": "Secret task", "task_type": "other"})
db = core.connect()
d = db.execute("SELECT published FROM assignments WHERE title='Secret task'").fetchone()
print("   saved as draft (published=0):", d["published"] == 0)
assert d["published"] == 0
db.close()
pg = get("/assignments")
print("   Publish button offered:", "/publish" in pg)
print("   listed in the table:", "Secret task" in pg)

print("\n5. THE PAGE STILL WORKS")
print("   homework page:", "<h1>Homework</h1>" in get("/homework"))
print("   swappable (music keeps playing):",
      "<script" not in re.search(r"<main[^>]*>(.*)</main>", pg, re.S).group(1))
srv.shutdown(); shutil.rmtree(tmp)
print("\nOne form does everything the two did.")
