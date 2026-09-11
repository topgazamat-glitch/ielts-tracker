"""Grade — see the assertions for what it guarantees.

Run me with:  python3 run_tests.py            (all of them)
              python3 tests/grade_test.py   (just this one)
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
g = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('T','TT',?)",
               (core.iso(core.now()),)).lastrowid
sid = db.execute("INSERT INTO students (name, group_id, active, token, created_at)"
      " VALUES ('Ali',?,1,'tok0000000000000000',?)", (g, core.iso(core.now()))).lastrowid
sid2 = db.execute("INSERT INTO students (name, group_id, active, token, created_at)"
      " VALUES ('Vali',?,1,'tok1111111111111111',?)", (g, core.iso(core.now()))).lastrowid
for lbl in ("grammar", "spelling", "structure"):
    db.execute("INSERT INTO tags (label) VALUES (?)", (lbl,))
plain = db.execute("INSERT INTO assignments (group_id, title, created_at, published)"
                   " VALUES (?,'Essay 1',?,1)", (g, core.iso(core.now()))).lastrowid
rub = db.execute("INSERT INTO assignments (group_id, title, created_at, published, rubric)"
                 " VALUES (?,'Task 2 essay',?,1,1)", (g, core.iso(core.now()))).lastrowid

def sub(student, aid, kind="photo", fname=None, when=None):
    s = db.execute("INSERT INTO submissions (student_id, assignment_id, created_at, kind)"
                   " VALUES (?,?,?,?)", (student, aid, when or core.iso(core.now()), kind)).lastrowid
    if fname:
        open(os.path.join(core.UPLOAD_DIR, fname), "wb").write(b"\xff\xfb\x90\x00" + b"\0"*8000)
        db.execute("INSERT INTO files (submission_id, filename, ord) VALUES (?,?,0)", (s, fname))
    return s

old = sub(sid, plain, fname="a.jpg", when=core.iso(core.now() - __import__("datetime").timedelta(days=5)))
db.execute("UPDATE submissions SET status='graded', score=6, note='Too short.',"
           " graded_at=? WHERE id=?", (core.iso(core.now()), old))
db.execute("INSERT INTO submission_tags (submission_id, tag_id) VALUES (?,1)", (old,))
voice = sub(sid, plain, kind="voice", fname="v.oga")
essay = sub(sid2, rub, fname="b.jpg")
db.commit(); db.close()

srv = server.Server(("127.0.0.1", 8811), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start(); time.sleep(0.4)
B = "http://127.0.0.1:8811"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(B + "/login", urllib.parse.urlencode({"password": "testpw123"}).encode()).read()
def get(u): return op.open(B + u).read().decode("utf-8")
def post(u, d): return op.open(B + u, urllib.parse.urlencode(d, doseq=True).encode()).read().decode("utf-8")

q = get("/queue")
print("1. SPEAKING  audio player present:", "<audio" in q and "v.oga" in q)
print("             not rendered as an image:", 'img src="/media/v.oga"' not in q)
assert "<audio" in q and 'img src="/media/v.oga"' not in q

print("2. HALF MARKS  half buttons on the pad:", 'data-v="7.5"' in q)
assert 'data-v="7.5"' in q

print("3. QUEUE LIST  jump links:", "/queue?id=" in q, "| names listed:",
      q.count("/queue?id=") >= 2)
assert "/queue?id=" in q

print("4. TEMPLATES   quick-note chips:", q.count('class="chip"'), "| editor:", "/notes/new" in q)
assert q.count('class="chip"') >= 6

print("5. PREVIOUS    last piece shown:", "Last time" in q, "| its note:", "Too short." in q,
      "| changeable:", "/regrade/%d" % old in q)
assert "Last time" in q and "Too short." in q

print("6. RECURRING   tag history shown:", "Keeps happening" in q and "grammar" in q)
assert "Keeps happening" in q

print("7. UNDO STRIP  present:", "Last marked" in q and "change it" in q)
assert "Last marked" in q

print("8. CRITERIA    on the rubric assignment:")
q2 = get("/queue?id=%d" % essay)
for _k, label, _h in core.CRITERIA:
    assert label in q2, label
print("             ", ", ".join(l for _k, l, _h in core.CRITERIA), "-> all present")
print("              plain assignment stays a single mark:",
      "Task response" not in q and 'id="f_score"' in q)
assert "Task response" not in q

print("\n--- marking works ---")
post("/grade", {"submission_id": essay, "c_task": "7", "c_coherence": "6",
                "c_lexis": "6.5", "c_grammar": "6", "note": "Good structure.",
                "tag": ["1", "2"]})
db = core.connect()
r = db.execute("SELECT score, note FROM submissions WHERE id=?", (essay,)).fetchone()
c = core.criteria_for(db, essay)
print("criteria stored:", c)
print("overall = average(7, 6, 6.5, 6) = 6.375 -> nearest half =", r["score"])
assert c == {"task": 7.0, "coherence": 6.0, "lexis": 6.5, "grammar": 6.0}
assert r["score"] == 6.5, r["score"]
tg = [x["tag_id"] for x in db.execute("SELECT tag_id FROM submission_tags WHERE submission_id=?", (essay,))]
print("tags saved:", sorted(tg)); assert sorted(tg) == [1, 2]
db.close()

print("\n--- correcting a mark ---")
page = get("/regrade/%d" % essay)
print("regrade page opens:", "Change a mark" in page)
print("shows what was given:", 'value="7.0"' in page or 'value="7"' in page)
post("/regrade", {"submission_id": essay, "c_task": "9", "c_coherence": "9",
                  "c_lexis": "9", "c_grammar": "9", "note": "Much better."})
db = core.connect()
r = db.execute("SELECT score, note FROM submissions WHERE id=?", (essay,)).fetchone()
print("changed to:", r["score"], "-", r["note"])
assert r["score"] == 9.0 and r["note"] == "Much better."

print("\n--- half marks save ---")
post("/grade", {"submission_id": voice, "score": "7.5", "note": ""})
r = db.execute("SELECT score FROM submissions WHERE id=?", (voice,)).fetchone()
print("saved score:", r["score"]); assert r["score"] == 7.5
print("rubbish refused:", core.mark_score("7.3"), core.mark_score("11"), core.mark_score("x"))
db.close()

print("\n--- quick notes ---")
db = core.connect()
fresh = db.execute("INSERT INTO submissions (student_id, assignment_id, created_at, kind)"
                   " VALUES (?,?,?,'photo')", (sid, plain, core.iso(core.now()))).lastrowid
db.commit(); db.close()
post("/notes/new", {"text": "Check your spelling throughout."})
q3 = get("/queue")
print("added:", "Check your spelling throughout." in q3)
db = core.connect()
n = db.execute("SELECT id FROM note_templates WHERE text=?", ("Check your spelling throughout.",)).fetchone()
db.close()
post("/notes/delete", {"id": n["id"]})
print("removed:", "Check your spelling throughout." not in get("/queue"))

print("\n--- voice plays with byte ranges ---")
r = urllib.request.Request(B + "/media/v.oga", headers={"Range": "bytes=0-99"})
try:
    x = op.open(r); print("  %s  %s  %d bytes  type=%s" % (
        x.status, dict(x.headers).get("Content-Range"), len(x.read()),
        dict(x.headers).get("Content-Type")))
    assert x.status == 206
except urllib.error.HTTPError as e:
    print("  FAILED", e.code); raise

print("\n--- the page stays swappable (music keeps playing) ---")
body = re.search(r"<main[^>]*>(.*)</main>", get("/queue"), re.S).group(1)
print("no inline script in main:", "<script" not in body)
assert "<script" not in body
srv.shutdown(); shutil.rmtree(tmp)
print("\nAll eight changes verified.")
