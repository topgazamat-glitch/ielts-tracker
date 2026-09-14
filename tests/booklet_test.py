"""Booklet — a handout and its answer key become a digital test.

Run me with:  python3 run_tests.py booklet
"""
import http.cookiejar
import json
import os
import re
import shutil
import sys
import tempfile
import threading
import time
import urllib.parse
import urllib.request
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None); os.environ["TEACHER_PASSWORD"] = "pw"
import core, server

print("1. TYPED ANSWERS ARE MARKED FORGIVINGLY, NOT LOOSELY")
for given, want, expect in (("the longest", "the longest", True),
                            ("The Longest.", "the longest", True),
                            ("  a feed ", "a feed", True),
                            ("don't", "don’t", True),
                            ("cheapest", "cheapest/the cheapest", True),
                            ("longer", "the longest", False),
                            ("", "anything", False),
                            ("feed", "a feed", False)):
    got = core.answer_matches(given, want)
    print("   %-14r vs %-22r -> %s" % (given, want, got))
    assert got == expect

print("\n2. A CONVERTED BOOKLET LOADS, IS SAT, AND IS MARKED")
core.init_db(); db = core.connect()
g = db.execute("INSERT INTO groups (name, join_code, level_id, created_at)"
               " VALUES ('214','A',3,?)", (core.iso(core.now()),)).lastrowid
db.execute("INSERT INTO students (name, group_id, active, token, created_at)"
           " VALUES ('Ali',?,1,'tok0000000000000000',?)", (g, core.iso(core.now())))
db.commit(); db.close()

data = {"level": "Pre-Intermediate", "number": 1,
        "title": "Unit 1 · Communication (1B+1D)", "passages": {},
        "questions": [
            {"num": 1, "kind": "mcq", "prompt": "1.3  Jin uses Instagram mainly for",
             "options": [{"letter": "A", "text": "photos"},
                         {"letter": "B", "text": "remembering birthdays"},
                         {"letter": "C", "text": "work"}], "answer": "B"},
            {"num": 2, "kind": "typed", "prompt": "1.4  to stay in contact with somebody",
             "options": [], "answer": "to keep in touch"},
            {"num": 3, "kind": "typed", "prompt": "1.4  the list of posts you see on an app",
             "options": [], "answer": "a feed"},
            {"num": 4, "kind": "yesno", "prompt": "1.8  Marc writes one blog post a week.",
             "options": [{"letter": "T", "text": "True"},
                         {"letter": "F", "text": "False"}], "answer": "T"},
        ]}
path = os.path.join(tmp, "booklet.json")
json.dump(data, open(path, "w"))

srv = server.Server(("127.0.0.1", 8882), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start(); time.sleep(0.4)
B = "http://127.0.0.1:8882"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(B + "/login", urllib.parse.urlencode({"password": "pw"}).encode()).read()
bd = "----b" + uuid.uuid4().hex
blob = open(path, "rb").read()
body = (("--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"b.json\"\r\n"
         "Content-Type: application/json\r\n\r\n" % bd).encode() + blob
        + ("\r\n--%s--\r\n" % bd).encode())
r = urllib.request.Request(B + "/tests/new", data=body)
r.add_header("Content-Type", "multipart/form-data; boundary=" + bd)
op.open(r)
db = core.connect()
t = db.execute("SELECT * FROM dtests").fetchone()
qs = core.test_questions(db, t["id"])
kinds = {}
for q, _o in qs:
    kinds[q["kind"]] = kinds.get(q["kind"], 0) + 1
print("   loaded %r: %d questions %s" % (t["title"], len(qs), kinds))
assert len(qs) == 4 and kinds.get("typed") == 2
db.execute("UPDATE dtests SET published=1 WHERE id=?", (t["id"],)); db.commit()
db.close()

print("\n3. A STUDENT TYPES THE ANSWERS")
so = urllib.request.build_opener()
paper = so.open(B + "/s/tok0000000000000000?tab=tests&t=%d" % t["id"]).read().decode()
print("   the paper shows the questions:", "stay in contact" in paper)
assert "stay in contact" in paper and "keep in touch" not in paper, \
    "the answer must not be on the page"
boxes = paper.count('class="typedin"')
print("   typed questions have a box to type in:", boxes)
assert boxes == 2, "a typed question with no box cannot be answered"
print("   the multiple choice still has radio buttons:",
      paper.count('type="radio"') >= 3)
db = core.connect(); qs = core.test_questions(db, t["id"]); db.close()
ids = {q["num"]: q["id"] for q, _o in qs}
answers = {"q%d" % ids[1]: "B",
           "q%d" % ids[2]: "To Keep In Touch.",     # sloppy but right
           "q%d" % ids[3]: "feed",                  # missing the article
           "q%d" % ids[4]: "T"}
so.open(B + "/s/tok0000000000000000/test/%d" % t["id"],
        urllib.parse.urlencode(answers).encode()).read()
db = core.connect()
a = db.execute("SELECT * FROM dattempts WHERE finished_at IS NOT NULL").fetchone()
print("   scored %d of %d  (case and a full stop forgiven, a missing article not)"
      % (a["score"], a["total"]))
assert a["score"] == 3 and a["total"] == 4
db.close()
srv.shutdown(); shutil.rmtree(tmp)
print("\nA handout becomes something that marks itself.")
