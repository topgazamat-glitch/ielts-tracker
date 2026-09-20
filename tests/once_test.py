"""An exam is sat once.

Run me with:  python3 run_tests.py once
              python3 tests/once_test.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import tempfile, threading, urllib.request, urllib.parse, time, http.cookiejar
tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None)

import core, server
core.init_db(); db = core.connect(); cfg = core.load_config()
gid = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES (?,?,?)",
                 ("114", "LX59FK", core.iso(core.now()))).lastrowid
lvl = db.execute("SELECT id FROM levels WHERE name='Elementary'").fetchone()["id"]
db.execute("UPDATE groups SET level_id=? WHERE id=?", (lvl, gid))
sid = core.add_student(db, "Dilnoza", gid)
token = db.execute("SELECT token FROM students WHERE id=?", (sid,)).fetchone()["token"]
tid = core.load_test(db, {
    "level": "Elementary", "number": 1, "title": "A mock",
    "minutes": 50, "strict": True, "once": True,
    "layout": '<p>1 <span data-mcq="1"></span></p>',
    "questions": [{"num": 1, "kind": "mcq", "prompt": "One", "answer": "A",
                   "options": [{"letter": "A", "text": "yes"},
                               {"letter": "B", "text": "no"}]}]})
db.execute("UPDATE dtests SET published=1 WHERE id=?", (tid,))
qid = db.execute("SELECT id FROM dquestions WHERE test_id=?", (tid,)).fetchone()["id"]
db.commit(); db.close()

srv = server.Server(("127.0.0.1", 8814), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
time.sleep(0.4)
base = "http://127.0.0.1:8814"
op = urllib.request.build_opener()

sit = "%s/s/%s?tab=tests&t=%d" % (base, token, tid)
page = op.open(sit).read().decode()
assert "Hand it in" in page, "the paper did not open"
print("Dilnoza opens the paper")

def hand_in(letter):
    op.open("%s/s/%s/test/%d" % (base, token, tid),
            urllib.parse.urlencode({"q%d" % qid: letter}).encode())
    d = core.connect()
    rows = d.execute("SELECT score FROM dattempts WHERE test_id=? AND student_id=?"
                     " AND finished_at IS NOT NULL", (tid, sid)).fetchall()
    d.close()
    return [r["score"] for r in rows]

print("  hands in a wrong answer ->", hand_in("B"))

page = op.open(sit).read().decode()
assert "Try it again" not in page, "an exam offered a second go"
assert "sat once" in page, "the page does not say why there is no second go"
print("  the result page offers no second go")

page = op.open(sit + "&again=1").read().decode()
assert "Hand it in" not in page, "again=1 reopened a sat exam"
print("  typing again=1 into the address bar does not reopen it")

got = hand_in("A")
assert got == [0], ("a second hand-in was accepted", got)
print("  a stale tab handing in a perfect paper changes nothing ->", got)

# a practice test is unchanged
d = core.connect()
d.execute("UPDATE dtests SET once=0 WHERE id=?", (tid,)); d.commit(); d.close()
page = op.open(sit).read().decode()
assert "Try it again" in page, "practice lost its second go"
print("practice tests still offer 'Try it again'")

srv.shutdown()
print("PASS  an exam is sat once, practice as often as it helps")
