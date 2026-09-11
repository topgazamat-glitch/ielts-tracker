"""Roster — see the assertions for what it guarantees.

Run me with:  python3 run_tests.py            (all of them)
              python3 tests/roster_test.py   (just this one)
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
FIXTURES = os.path.join(ROOT, "tests", "fixtures")

import tempfile, shutil, threading, time, re, http.cookiejar
import urllib.request, urllib.parse
from datetime import timedelta
tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None); os.environ["TEACHER_PASSWORD"] = "testpw123"

import core, server
core.init_db(); db = core.connect()
g1 = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('Beginner','B1',?)",
                (core.iso(core.now()),)).lastrowid
g2 = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('Elementary','E1',?)",
                (core.iso(core.now()),)).lastrowid
names = ["Aziz", "Bekzod", "Dilnoza", "Malika", "Rustam"]
ids = []
for i, nm in enumerate(names):
    ids.append(db.execute("INSERT INTO students (name, group_id, active, token, telegram_id,"
        " created_at) VALUES (?,?,1,?,?,?)", (nm, g1, "tok%016d" % i,
        1000 + i if i < 4 else None, core.iso(core.now()))).lastrowid)
a = db.execute("INSERT INTO assignments (group_id, title, created_at, published)"
               " VALUES (?,'Essay',?,1)", (g1, core.iso(core.now()))).lastrowid
db.execute("INSERT INTO submissions (student_id, assignment_id, status, score, created_at,"
           " kind) VALUES (?,?,'graded',7,?,'photo')",
           (ids[0], a, core.iso(core.now() - timedelta(days=2))))
db.execute("INSERT INTO submissions (student_id, assignment_id, status, score, created_at,"
           " kind) VALUES (?,?,'graded',6,?,'photo')",
           (ids[1], a, core.iso(core.now() - timedelta(days=20))))
db.commit(); db.close()
srv = server.Server(("127.0.0.1", 8815), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start(); time.sleep(0.4)
B = "http://127.0.0.1:8815"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(B + "/login", urllib.parse.urlencode({"password": "testpw123"}).encode()).read()
def get(u): return op.open(B + u).read().decode("utf-8")
def post(u, d): return op.open(B + u, urllib.parse.urlencode(d, doseq=True).encode()).read().decode("utf-8")

pg = get("/roster")
print("1. ACTIONS ON THE LIST")
for what, tok in [("pause", "/pause"), ("delete", "/delete"), ("move class", "/move"),
                  ("bulk", "/students/bulk"), ("add by hand", "/students/new")]:
    print("   %-12s ->" % what, tok in pg); assert tok in pg
print("   delete warns it is final:", "cannot be undone" in pg)
assert "cannot be undone" in pg

print("\n2. LAST SEEN")
print("   Aziz (2d ago) shown as recent:", "2d ago" in pg)
print("   Bekzod (20d) flagged:", "20d ago" in pg and "risk" in pg)
print("   never-active flagged:", "never" in pg)
assert "2d ago" in pg and "20d ago" in pg and "never" in pg

print("\n3. NO-BOT MARKER")
print("   Rustam has no telegram:", "no bot" in pg)
assert "no bot" in pg

print("\n4. FILTERING")
b = get("/roster?group=%d" % g1); e = get("/roster?group=%d" % g2)
print("   Beginner shows its 5:", all(n in b for n in names))
print("   Elementary is empty: ", "Nobody matches" in e and not any(n in e for n in names))
assert all(n in b for n in names) and not any(n in e for n in names)
print("   search:", "Dilnoza" in get("/roster?q=Diln") and "Aziz" not in get("/roster?q=Diln"))
assert "Aziz" not in get("/roster?q=Diln")

print("\n5. MOVE ONE STUDENT")
post("/students/%d/move" % ids[0], {"group_id": g2})
db = core.connect()
print("   Aziz now in:", db.execute("SELECT g.name FROM students s JOIN groups g"
      " ON g.id=s.group_id WHERE s.id=?", (ids[0],)).fetchone()["name"])
assert db.execute("SELECT group_id FROM students WHERE id=?", (ids[0],)).fetchone()["group_id"] == g2
db.close()

print("\n6. BULK MOVE AND PAUSE")
post("/students/bulk", {"id": [ids[1], ids[2]], "do": "move", "group_id": g2})
db = core.connect()
moved = [r["name"] for r in db.execute("SELECT name FROM students WHERE group_id=?", (g2,))]
print("   in Elementary now:", sorted(moved)); assert len(moved) == 3
db.close()
post("/students/bulk", {"id": [ids[3], ids[4]], "do": "pause"})
db = core.connect()
print("   paused:", [r["name"] for r in db.execute("SELECT name FROM students WHERE active=0")])
assert db.execute("SELECT COUNT(*) c FROM students WHERE active=0").fetchone()["c"] == 2
db.close()
print("   paused hidden by default:", "Malika" not in get("/roster"))
print("   shown under Paused:", "Malika" in get("/roster?show=paused"))
post("/students/bulk", {"id": [ids[3]], "do": "resume"})
db = core.connect()
assert db.execute("SELECT active FROM students WHERE id=?", (ids[3],)).fetchone()["active"] == 1
print("   resumed: True"); db.close()

print("\n7. ADD BY HAND")
post("/students/new", {"name": "Nodira", "group_id": g1})
db = core.connect()
n = db.execute("SELECT * FROM students WHERE name='Nodira'").fetchone()
print("   created with a page link:", bool(n["token"]), "| no telegram:", n["telegram_id"] is None)
assert n["token"] and n["telegram_id"] is None
db.close()

print("\n8. DELETE CLEANS UP PROPERLY")
db = core.connect()
db.execute("INSERT INTO bot_state (telegram_id, step) VALUES (1000, 'x')")
db.commit(); db.close()
post("/students/%d/delete" % ids[0], {})
db = core.connect()
print("   student gone:", db.execute("SELECT COUNT(*) c FROM students WHERE id=?",
      (ids[0],)).fetchone()["c"] == 0)
print("   their submissions gone:", db.execute("SELECT COUNT(*) c FROM submissions"
      " WHERE student_id=?", (ids[0],)).fetchone()["c"] == 0)
left = db.execute("SELECT COUNT(*) c FROM bot_state WHERE telegram_id=1000").fetchone()["c"]
print("   stale bot state cleared:", left == 0, "(was a bug: cleaned after the row had gone)")
assert left == 0
db.close()

print("\n9. PAGE STAYS SWAPPABLE")
pg = get("/roster")
print("   no inline script in main:",
      "<script" not in re.search(r"<main[^>]*>(.*)</main>", pg, re.S).group(1))
srv.shutdown(); shutil.rmtree(tmp)
print("\nRoster actions work.")
