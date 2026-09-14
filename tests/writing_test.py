"""Writing — typed answers instead of photographs of handwriting.

Run me with:  python3 run_tests.py writing
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
db.execute("INSERT INTO students (name, group_id, active, token, created_at)"
           " VALUES ('Ali',?,1,'tok0000000000000000',?)", (g, core.iso(core.now())))
db.commit(); db.close()

srv = server.Server(("127.0.0.1", 8880), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start(); time.sleep(0.4)
B = "http://127.0.0.1:8880"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(B + "/login", urllib.parse.urlencode({"password": "pw"}).encode()).read()
def post(u, d, o=None):
    return (o or op).open(B + u, urllib.parse.urlencode(d, doseq=True).encode()).read().decode()
def get(u, o=None): return (o or op).open(B + u).read().decode()
me = urllib.request.build_opener()

QUESTION = ("Some people think students should study alone. "
            "Discuss both views and give your own opinion.")
print("1. THE TEACHER SETS A WRITING TASK")
post("/assignments/list", {"group_id": g, "items": "Task 2 essay",
     "due": "2026-12-01", "due_time": "23:59", "publish": "1",
     "prompt": QUESTION, "min_words": "250", "minutes": "40"})
db = core.connect()
a = db.execute("SELECT * FROM assignments").fetchone()
print("   %r  min %s words, %s minutes" % (a["title"], a["min_words"], a["minutes"]))
assert a["prompt"] == QUESTION and a["min_words"] == 250 and a["minutes"] == 40
db.close()

print("\n2. THE STUDENT GETS A PAPER, NOT A FORM")
lst = get("/s/tok0000000000000000?tab=write", me)
print("   the task is listed:", "Task 2 essay" in lst and "not started" in lst)
page = get("/s/tok0000000000000000?tab=write&a=%d" % a["id"], me)
print("   the question is on the page:", QUESTION[:30] in page)
print("   there is a sheet to write on:", 'id="answer"' in page)
print("   a word count and a clock:", 'id="wordcount"' in page and 'id="clock"' in page)
print("   the question folds away on a phone:", 'id="qtoggle"' in page)
assert QUESTION[:30] in page and 'id="answer"' in page and 'id="qtoggle"' in page
sub = int(re.search(r'data-sub="(\d+)"', page).group(1))
print("   it knows the minimum:", re.search(r'data-min="(\d+)"', page).group(1), "words")

print("\n3. IT SAVES WHILE THEY TYPE")
r = me.open(B + "/s/tok0000000000000000/write/%d/save" % sub,
            urllib.parse.urlencode({"answer": "One two three four five.",
                                    "seconds": "65"}).encode())
print("   the quiet save replies:", r.read().decode()[:40])
db = core.connect()
row = db.execute("SELECT * FROM submissions WHERE id=?", (sub,)).fetchone()
print("   stored: %d words, still a draft: %s" % (row["words"], bool(row["draft"])))
assert row["words"] == 5 and row["draft"] == 1
print("   it is not in the marking queue yet:",
      db.execute("SELECT COUNT(*) c FROM submissions WHERE status='pending'"
                 " AND draft=0").fetchone()["c"] == 0)
db.close()

print("\n4. COMING BACK FINDS THE WORK STILL THERE")
again = get("/s/tok0000000000000000?tab=write&a=%d" % a["id"], me)
print("   what was typed is in the box:", "One two three four five." in again)
assert "One two three four five." in again

print("\n5. HANDING IN")
essay = "Many people believe that studying alone is better. " * 12
post("/s/tok0000000000000000/write/%d" % sub,
     {"answer": essay, "seconds": "900", "hand_in": "1"}, me)
db = core.connect()
row = db.execute("SELECT * FROM submissions WHERE id=?", (sub,)).fetchone()
print("   %d words, draft: %s, waiting to be marked: %s"
      % (row["words"], bool(row["draft"]), row["status"]))
assert row["draft"] == 0 and row["words"] == 96 and row["status"] == "pending"
db.close()
done = get("/s/tok0000000000000000?tab=write&a=%d" % a["id"], me)
print("   the student sees it is handed in:", "Handed in" in done)
print("   and can read it back:", "studying alone is better" in done)

print("\n6. THE TEACHER READS TYPED WORK, NOT A BROKEN PHOTO")
q = get("/queue")
print("   the question is shown beside it:", QUESTION[:30] in q)
print("   the essay is shown:", "studying alone is better" in q)
print("   no missing image:", "Nothing attached" not in q)
print("   the time spent is noted:", "min at the keyboard" in q)
assert QUESTION[:30] in q and "studying alone is better" in q

print("\n7. IT MARKS LIKE ANYTHING ELSE")
sid = re.search(r'name="submission_id" value="(\d+)"', q).group(1)
post("/grade", {"submission_id": sid, "score": "7.5", "note": "Good structure."})
db = core.connect()
row = db.execute("SELECT score, note, status FROM submissions WHERE id=?", (sub,)).fetchone()
print("   marked %s, %r, %s" % (row["score"], row["note"], row["status"]))
assert row["score"] == 7.5 and row["status"] == "graded"
db.close()

print("\n8. THE PAGE STAYS SWAPPABLE")
body = re.search(r"<main[^>]*>(.*)</main>", get("/queue"), re.S).group(1)
print("   no inline script in main:", "<script" not in body)
assert "<script" not in body
srv.shutdown(); shutil.rmtree(tmp)
print("\nStudents can type instead of photographing their handwriting.")
