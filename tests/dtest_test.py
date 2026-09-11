"""Dtest — see the assertions for what it guarantees.

Run me with:  python3 run_tests.py            (all of them)
              python3 tests/dtest_test.py   (just this one)
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
FIXTURES = os.path.join(ROOT, "tests", "fixtures")

import tempfile, shutil, threading, time, re, json, uuid, http.cookiejar
import urllib.request, urllib.parse
tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None); os.environ["TEACHER_PASSWORD"] = "testpw123"

import core, server
core.init_db(); db = core.connect()
lid = db.execute("SELECT id FROM levels WHERE name='Pre-Intermediate'").fetchone()["id"]
g = db.execute("INSERT INTO groups (name, join_code, level_id, created_at)"
               " VALUES ('PreInt','PI1',?,?)", (lid, core.iso(core.now()))).lastrowid
db.execute("INSERT INTO students (name, group_id, active, token, created_at)"
           " VALUES ('Ali',?,1,'tok0000000000000000',?)", (g, core.iso(core.now())))
db.commit(); db.close()
srv = server.Server(("127.0.0.1", 8822), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start(); time.sleep(0.5)
B = "http://127.0.0.1:8822"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(B + "/login", urllib.parse.urlencode({"password": "testpw123"}).encode()).read()
def get(u, o=None): return (o or op).open(B + u).read().decode("utf-8")
def post(u, d, o=None):
    return (o or op).open(B + u, urllib.parse.urlencode(d, doseq=True).encode()).read().decode("utf-8")

# --- load the extracted json through the real upload form
data = open(os.environ["CLAUDE_JOB_DIR"] + "/tmp/test01_full.json", "rb").read()
bd = "----t" + uuid.uuid4().hex
body = (("--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"t.json\"\r\n"
         "Content-Type: application/json\r\n\r\n" % bd).encode() + data
        + ("\r\n--%s--\r\n" % bd).encode())
r = urllib.request.Request(B + "/tests/new", data=body)
r.add_header("Content-Type", "multipart/form-data; boundary=" + bd)
op.open(r)
db = core.connect()
t = db.execute("SELECT * FROM dtests").fetchone()
qs = core.test_questions(db, t["id"])
print("1. LOADED  %r  level=%s  questions=%d  passage=%s" % (
    t["title"], t["level_id"] == lid, len(qs), bool(t["passage"])))
assert len(qs) == 15 and t["level_id"] == lid
kinds = {}
for q, o in qs:
    kinds[q["kind"]] = kinds.get(q["kind"], 0) + 1
print("   kinds:", kinds, "| options per question:", sorted({len(o) for _q, o in qs}))
db.close()

print("\n2. THE KEY ARRIVED WITH THE FILE")
db = core.connect()
keyed = db.execute("SELECT COUNT(*) c FROM dquestions WHERE test_id=? AND answer IS NOT NULL",
                   (t["id"],)).fetchone()["c"]
imgs = db.execute("SELECT COUNT(*) c FROM dquestions WHERE test_id=? AND image IS NOT NULL",
                  (t["id"],)).fetchone()["c"]
print("   answers set on load: %d of 15 | passages attached: %d" % (keyed, imgs))
assert keyed == 15 and imgs == 2
print("   the passage files are on disk:", all(os.path.isfile(
    os.path.join(core.MATERIAL_DIR, r["image"])) for r in db.execute(
    "SELECT image FROM dquestions WHERE image IS NOT NULL")))
db.close()

print("\n3. SET THE ANSWER KEY")
KEY = {11:"A",12:"B",13:"B",14:"A",15:"B",16:"C",17:"D",18:"A",19:"B",20:"C",
       21:"B",22:"A",23:"B",24:"B",25:"C"}
db = core.connect()
qs = core.test_questions(db, t["id"])
form = {}
for q, _o in qs:
    form["q%d" % q["id"]] = KEY[q["num"]]
db.close()
post("/tests/%d/key" % t["id"], form)
db = core.connect()
done = db.execute("SELECT COUNT(*) c FROM dquestions WHERE test_id=? AND answer IS NOT NULL",
                  (t["id"],)).fetchone()["c"]
print("   answers set: %d of 15 | ready: %s" % (done, core.test_ready(db, t["id"])))
assert done == 15 and core.test_ready(db, t["id"])
db.close()

print("\n4. PUBLISH")
post("/tests/%d/publish" % t["id"], {})
db = core.connect()
assert db.execute("SELECT published FROM dtests WHERE id=?", (t["id"],)).fetchone()["published"] == 1
print("   published: True")
db.close()

print("\n5. A STUDENT SITS IT")
so = urllib.request.build_opener()
lst = get("/s/tok0000000000000000?tab=tests", so)
print("   test listed:", "Practice Test 1" in lst)
paper = get("/s/tok0000000000000000?tab=tests&t=%d" % t["id"], so)
radios = len(re.findall(r'type="radio"', paper))
print("   questions on screen: %d radio buttons across 15 questions" % radios)
print("   the passage is shown:", "New Home" in paper)
assert "New Home" in paper

db = core.connect(); qs = core.test_questions(db, t["id"]); db.close()
answers = {}
for i, (q, _o) in enumerate(qs):
    # get 11 right, 4 deliberately wrong
    answers["q%d" % q["id"]] = KEY[q["num"]] if i < 11 else ("A" if KEY[q["num"]] != "A" else "B")
post("/s/tok0000000000000000/test/%d" % t["id"], answers, so)
db = core.connect()
a = db.execute("SELECT * FROM dattempts WHERE finished_at IS NOT NULL").fetchone()
print("   marked instantly: %d of %d  (11 right on purpose)" % (a["score"], a["total"]))
assert a["score"] == 11 and a["total"] == 15
db.close()

print("\n6. THE STUDENT SEES WHAT THEY GOT WRONG")
res = get("/s/tok0000000000000000?tab=tests&t=%d" % t["id"], so)
print("   score shown:", "11" in res)
print("   right answers marked:", res.count('class="opt right"'))
print("   their wrong picks marked:", res.count('class="opt chosen"'))
assert res.count('class="opt right"') == 15 and res.count('class="opt chosen"') == 4

print("\n7. THE TEACHER SEES THE RESULT")
tp = get("/tests/%d" % t["id"])
print("   listed on the test page:", "Ali" in tp and "11" in tp)
assert "Ali" in tp
print("   swappable page:", "<script" not in re.search(r"<main[^>]*>(.*)</main>", tp, re.S).group(1))
srv.shutdown(); shutil.rmtree(tmp)
print("\nA digital test works end to end.")
