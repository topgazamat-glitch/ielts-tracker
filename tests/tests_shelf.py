"""Tests shelf — see the assertions for what it guarantees.

Run me with:  python3 run_tests.py            (all of them)
              python3 tests/tests_shelf.py   (just this one)
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
FIXTURES = os.path.join(ROOT, "tests", "fixtures")

import tempfile, shutil, threading, time, subprocess, re, http.cookiejar
import urllib.request, urllib.parse
tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None); os.environ["TEACHER_PASSWORD"] = "testpw123"

import core, server
core.init_db()
srv = server.Server(("127.0.0.1", 8821), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start(); time.sleep(0.5)
B = "http://127.0.0.1:8821"
src = os.environ["CLAUDE_JOB_DIR"] + "/tmp/b1"
env = dict(os.environ, DATA_DIR=tmp, TEACHER_PASSWORD="testpw123")
R = ROOT

def run(*a):
    return subprocess.run([sys.executable, "upload_tests.py", *a],
                          capture_output=True, text=True, env=env, cwd=R)

print("--- upload the 20 papers ---")
r = run(src, "--level", "Pre-Intermediate", "--site", B, "--upload")
print(r.stdout.strip().splitlines()[-1] if r.stdout else r.stderr[-400:])

# a fake audio and answer key for Test 1, to prove they land together
extra = tempfile.mkdtemp()
open(os.path.join(extra, "Test 01 audio.mp3"), "wb").write(b"\xff\xfb\x90\x00" + b"\0" * 40000)
open(os.path.join(extra, "Test 01 answers.pdf"), "wb").write(b"%PDF-1.4\n" + b"\0" * 500)
print("\n--- add Test 1's audio and answers ---")
r = run(extra, "--level", "Pre-Intermediate", "--site", B, "--section", "Audio", "--upload")
print("  audio:", r.stdout.strip().splitlines()[-1] if r.stdout else r.stderr[-300:])

jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(B + "/login", urllib.parse.urlencode({"password": "testpw123"}).encode()).read()
def get(u): return op.open(B + u).read().decode("utf-8")

db = core.connect()
lid = db.execute("SELECT id FROM levels WHERE name='Pre-Intermediate'").fetchone()["id"]
n = db.execute("SELECT COUNT(*) c FROM materials").fetchone()["c"]
byunit = db.execute("SELECT unit, COUNT(*) c FROM materials GROUP BY unit"
                    " ORDER BY unit").fetchall()
print("\nmaterials: %d | per test: %s" % (n, {r["unit"]: r["c"] for r in byunit}))
db.close()
assert n == 22 and byunit[0]["unit"] == 1 and byunit[0]["c"] == 3

print("\n--- the shelf ---")
shelf = get("/materials?level=%d&c=practice" % lid)
buttons = re.findall(r">Test (\d+)<", shelf)
print("  test buttons shown: %d  (%s ... %s)" % (len(buttons), buttons[0], buttons[-1]))
assert len(buttons) == 20
print("  Test 1 shows 3 files:", ">3 files<" in shelf)
print("  empty tests marked:", shelf.count("empty") >= 19)

print("\n--- inside Test 1 ---")
one = get("/materials?level=%d&c=practice&u=1" % lid)
for kind in ("Paper", "Audio"):
    print("  labelled %-7s %s" % (kind, ">%s<" % kind in one))
print("  audio has a player:", "<audio" in one)
print("  breadcrumb says Test 1:", "Test 1" in one and "Unit 1" not in one)
assert "<audio" in one and "Unit 1" not in one
names = re.findall(r'/materials/\d+/file">([^<]+)</a>', one)
print("  files:", names)
assert len(names) == 3

print("\n--- a student sees the same ---")
db = core.connect()
g = db.execute("INSERT INTO groups (name, join_code, level_id, created_at)"
               " VALUES ('PreInt','PI1',?,?)", (lid, core.iso(core.now()))).lastrowid
db.execute("INSERT INTO students (name, group_id, active, token, created_at)"
           " VALUES ('Ali',?,1,'tok0000000000000000',?)", (g, core.iso(core.now())))
db.commit(); db.close()
sp = urllib.request.urlopen(B + "/s/tok0000000000000000?tab=materials&c=practice").read().decode()
print("  student sees test buttons:", len(re.findall(r">Test \d+<", sp)))
srv.shutdown(); shutil.rmtree(tmp); shutil.rmtree(extra)
print("\nTwenty buttons, each holding its own paper, audio and answers.")
