"""Delete student — see the assertions for what it guarantees.

Run me with:  python3 run_tests.py            (all of them)
              python3 tests/delete_student_test.py   (just this one)
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
FIXTURES = os.path.join(ROOT, "tests", "fixtures")

import tempfile, shutil, re, json, threading, time, http.cookiejar
import urllib.request, urllib.parse
from datetime import timedelta
tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None); os.environ["TEACHER_PASSWORD"] = "pw"

import core, server
core.init_db(); db = core.connect(); cfg = core.load_config()

g = db.execute("INSERT INTO groups (name, join_code, level_id, created_at)"
               " VALUES ('114','A',2,?)", (core.iso(core.now()),)).lastrowid
sid = db.execute("INSERT INTO students (name, group_id, active, token, telegram_id,"
    " created_at) VALUES ('Ali',?,1,'tok0000000000000000',999,?)",
    (g, core.iso(core.now()))).lastrowid

# give this student a row in every table that points at students
a = db.execute("INSERT INTO assignments (group_id, title, created_at, published, due_at)"
    " VALUES (?,?,?,1,?)", (g, "HW", core.iso(core.now()),
    core.iso(core.now() + timedelta(days=1)))).lastrowid
sub = db.execute("INSERT INTO submissions (student_id, assignment_id, status, score,"
    " created_at, kind) VALUES (?,?,'graded',8,?,'photo')",
    (sid, a, core.iso(core.now()))).lastrowid
db.execute("INSERT INTO files (submission_id, filename, ord) VALUES (?,?,0)", (sub, "p.jpg"))
open(os.path.join(core.UPLOAD_DIR, "p.jpg"), "wb").write(b"x")
db.execute("INSERT INTO tags (label) VALUES ('grammar')")
db.execute("INSERT INTO submission_tags (submission_id, tag_id) VALUES (?,1)", (sub,))
db.execute("INSERT INTO criteria_scores (submission_id, key, score) VALUES (?,'task',7)", (sub,))
wl = db.execute("INSERT INTO word_lists (title, active, created_at) VALUES ('U',1,?)",
                (core.iso(core.now()),)).lastrowid
for w in ("a", "b", "c", "d"):
    db.execute("INSERT INTO words (list_id, term, translation) VALUES (?,?,?)", (wl, w, w))
wid = db.execute("SELECT id FROM words LIMIT 1").fetchone()["id"]
db.execute("INSERT INTO word_progress (student_id, word_id, seen, correct, streak,"
           " next_due, last_seen) VALUES (?,?,1,1,1,?,?)",
           (sid, wid, core.iso(core.now()), core.iso(core.now())))
db.execute("INSERT INTO quiz_sessions (student_id, list_id, started_at)"
           " VALUES (?,?,?)", (sid, wl, core.iso(core.now())))
db.execute("INSERT INTO questions (student_id, text, created_at) VALUES (?,?,?)",
           (sid, "why?", core.iso(core.now())))
db.execute("INSERT INTO parents (student_id, token, created_at) VALUES (?,?,?)",
           (sid, "ptok", core.iso(core.now())))
db.execute("INSERT INTO lesson_marks (student_id, day, punctuality, behaviour,"
           " participation, created_at) VALUES (?,?,4,4,4,?)",
           (sid, core.local_day(core.now(), cfg), core.iso(core.now())))
db.execute("INSERT INTO goals (student_id, listening, updated_at) VALUES (?,6.5,?)",
           (sid, core.iso(core.now())))
db.execute("INSERT INTO bot_state (telegram_id, step) VALUES (999,'x')")
db.commit()
game = core.make_game(db, g, wl, q_count=2)
gid = game["id"] if isinstance(game, dict) else game
core.join_game(db, gid, sid)
q = db.execute("SELECT id FROM game_questions WHERE game_id=? LIMIT 1", (gid,)).fetchone()
db.execute("INSERT INTO game_answers (game_id, question_id, student_id, choice,"
           " correct, ms) VALUES (?,?,?,0,1,900)", (gid, q["id"], sid))
t = db.execute("INSERT INTO dtests (title, published, created_at) VALUES ('T',1,?)",
               (core.iso(core.now()),)).lastrowid
dq = db.execute("INSERT INTO dquestions (test_id, num, kind, prompt, answer)"
                " VALUES (?,1,'mcq','q','A')", (t,)).lastrowid
att = core.start_attempt(db, t, sid)
core.submit_attempt(db, att, {dq: "A"})
db.execute("INSERT INTO seasons (no, started_at, closed_at, winner_id, winner_name,"
           " winner_points, standing) VALUES (1,?,?,?,'Ali',5.0,'[]')",
           (core.iso(core.now()), core.iso(core.now()), sid))
db.commit()

# every table that points at students must have a row for them, or the test proves nothing
import re as _re
src = open(os.path.join(ROOT, "core.py")).read()
refs = []
for m in _re.finditer(r"CREATE TABLE IF NOT EXISTS (\w+) \((.*?)\n\s*\);", src, _re.S):
    for line in m.group(2).splitlines():
        if "REFERENCES students(id)" in line:
            refs.append((m.group(1), line.strip().split()[0]))
print("tables pointing at students:", len(refs))
missing = []
for table, col in refs:
    n = db.execute("SELECT COUNT(*) c FROM %s WHERE %s=?" % (table, col), (sid,)).fetchone()["c"]
    if not n:
        missing.append(table)
    print("   %-16s %-12s rows for this student: %d" % (table, col, n))
assert not missing, "the test does not cover: %s" % missing
db.close()

print("\nDeleting through the web page, the way the teacher does:")
srv = server.Server(("127.0.0.1", 8860), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start(); time.sleep(0.4)
B = "http://127.0.0.1:8860"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(B + "/login", urllib.parse.urlencode({"password": "pw"}).encode()).read()
r = op.open(B + "/students/%d/delete" % sid, b"")
page = r.read().decode("utf-8", "replace")
print("   response:", r.status, "| error page:", "Something broke" in page)
assert "Something broke" not in page

db = core.connect()
left = db.execute("SELECT COUNT(*) c FROM students WHERE id=?", (sid,)).fetchone()["c"]
print("   student gone:", left == 0)
assert left == 0
still = []
for table, col in refs:
    if table == "students":
        continue
    n = db.execute("SELECT COUNT(*) c FROM %s WHERE %s=?" % (table, col), (sid,)).fetchone()["c"]
    if n:
        still.append((table, n))
print("   rows left pointing at them:", still or "none")
assert not still or still == [("seasons", 0)]
print("   the record book keeps the winner's name:",
      db.execute("SELECT winner_name, winner_id FROM seasons").fetchone()["winner_name"])
print("   their bot conversation is cleared:",
      db.execute("SELECT COUNT(*) c FROM bot_state WHERE telegram_id=999").fetchone()["c"] == 0)
print("   no dangling test answers:",
      db.execute("SELECT COUNT(*) c FROM dresponses").fetchone()["c"] == 0)
db.close(); srv.shutdown(); shutil.rmtree(tmp)
print("\nA student who did everything can be deleted.")
