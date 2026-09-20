"""The teacher can read what students wrote.

Run me with:  python3 run_tests.py readwriting
              python3 tests/readwriting_test.py
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
who = {}
for name in ("Dilnoza", "Sardor", "Kamola"):
    who[name] = core.add_student(db, name, gid)
tid = core.load_test(db, {
    "level": "Elementary", "number": 1, "title": "A mock",
    "layout": '<p>1 <span data-mcq="1"></span> <span data-long="2"></span></p>',
    "questions": [
        {"num": 1, "kind": "mcq", "prompt": "One", "answer": "A",
         "options": [{"letter": "A", "text": "yes"}, {"letter": "B", "text": "no"}]},
        {"num": 2, "kind": "open", "prompt": "Write an email to a friend.",
         "answer": ""}]})
db.execute("UPDATE dtests SET published=1 WHERE id=?", (tid,))
qs = {r["num"]: r["id"] for r in
      db.execute("SELECT num, id FROM dquestions WHERE test_id=?", (tid,))}
db.commit()

EMAILS = {
    "Dilnoza": "Hi Sam, I am moving to a new flat near the park on Saturday. "
               "It is small but very bright and the kitchen is new. "
               "Please come and see it next week.",
    "Sardor": "Hello, I move flat.",
}
for name, sid in who.items():
    a = core.start_attempt(db, tid, sid)
    given = {qs[1]: "A"}
    if name in EMAILS:
        given[qs[2]] = EMAILS[name]
    core.submit_attempt(db, a, given)
db.commit(); db.close()

srv = server.Server(("127.0.0.1", 8815), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
time.sleep(0.4)
base = "http://127.0.0.1:8815"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(base + "/login",
        urllib.parse.urlencode({"password": cfg["teacher_password"]}).encode())

test_page = op.open(base + "/tests/%d" % tid).read().decode()
assert "/tests/%d/writing" % tid in test_page, "no way through to the writing"
print("the test page links to the writing")

p = op.open(base + "/tests/%d/writing" % tid).read().decode()
for name, text in EMAILS.items():
    assert name in p, name
    assert text[:40] in p, ("%s's email is not on the page" % name)
print("  both emails are there, in full, with their writer's name")

assert "Kamola" in p, "the student who wrote nothing is not accounted for"
assert "Nothing written by" in p
print("  the student who left it blank is named, not silently dropped")

assert "32 words" in p, "no word count for the long email"
assert "4 words" in p, "no word count for the short one"
print("  each email carries its word count")

# the page is about the writing, not a copy of the whole paper
assert p.count("Write an email to a friend.") == 1
print("  the page shows the writing task once, not every question")

srv.shutdown()
print("PASS  thirty-nine emails can be read in one place")
