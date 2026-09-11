"""Grammar — see the assertions for what it guarantees.

Run me with:  python3 run_tests.py            (all of them)
              python3 tests/grammar_test.py   (just this one)
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
FIXTURES = os.path.join(ROOT, "tests", "fixtures")

import tempfile, shutil, threading, time, json, re, http.cookiejar
import urllib.request, urllib.parse
tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None); os.environ["TEACHER_PASSWORD"] = "testpw123"

import core, server
core.init_db(); db = core.connect()
g = db.execute("INSERT INTO groups (name, join_code, level_id, created_at)"
               " VALUES ('114','E1',2,?)", (core.iso(core.now()),)).lastrowid
db.execute("INSERT INTO students (name, group_id, active, token, created_at)"
           " VALUES ('Ali',?,1,'tok0000000000000000',?)", (g, core.iso(core.now())))
db.commit(); db.close()
srv = server.Server(("127.0.0.1", 8830), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start(); time.sleep(0.5)
B = "http://127.0.0.1:8830"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(B + "/login", urllib.parse.urlencode({"password": "testpw123"}).encode()).read()

txt = open(os.environ["CLAUDE_JOB_DIR"] + "/tmp/comparatives.txt").read()
op.open(B + "/vocab/new", urllib.parse.urlencode({
    "title": "Comparatives & Superlatives", "source": "Grammar", "unit": "",
    "group_id": "", "kind": "grammar", "words": txt}).encode()).read()

db = core.connect()
wl = db.execute("SELECT * FROM word_lists").fetchone()
ws = db.execute("SELECT * FROM words WHERE list_id=? ORDER BY ord", (wl["id"],)).fetchall()
print("1. LIST  %r  kind=%s  questions=%d" % (wl["title"], wl["kind"], len(ws)))
assert wl["kind"] == "grammar" and len(ws) == 20
own = [w for w in ws if w["options"]]
print("   each carries its own wrong answers:", len(own))
assert len(own) == 20

print("\n2. THE GAME USES THEM, NOT OTHER ROWS' ANSWERS")
game = core.make_game(db, g, wl["id"], q_count=20)
gid = game["id"] if isinstance(game, dict) else game
qs = db.execute("SELECT * FROM game_questions WHERE game_id=? ORDER BY ord", (gid,)).fetchall()
print("   questions drawn:", len(qs))
bad = 0
for q in qs[:20]:
    w = db.execute("SELECT * FROM words WHERE id=?", (q["word_id"],)).fetchone()
    opts = json.loads(q["options"])
    mine = set(json.loads(w["options"]) + [w["translation"]])
    if set(opts) != mine or opts[q["answer"]] != w["translation"]:
        bad += 1
print("   every question's four options are its own, and the marked answer is right:",
      bad == 0)
assert bad == 0
for q in qs[:3]:
    w = db.execute("SELECT term, translation FROM words WHERE id=?", (q["word_id"],)).fetchone()
    o = json.loads(q["options"])
    print("     %-44s %s   [correct: %s]" % (w["term"][:44], o, o[q["answer"]]))
db.close()

print("\n3. A VOCABULARY LIST STILL BEHAVES AS BEFORE")
op.open(B + "/vocab/new", urllib.parse.urlencode({
    "title": "Unit 1", "group_id": "", "words":
    "apple = olma\nbook = kitob\ncat = mushuk\ndog = it\nhouse = uy"}).encode()).read()
db = core.connect()
v = db.execute("SELECT * FROM word_lists WHERE title='Unit 1'").fetchone()
print("   kind:", v["kind"])
vg = core.make_game(db, g, v["id"], q_count=5)
vgid = vg["id"] if isinstance(vg, dict) else vg
q = db.execute("SELECT * FROM game_questions WHERE game_id=? LIMIT 1", (vgid,)).fetchone()
o = json.loads(q["options"])
print("   options borrowed from the list, as before:", o)
assert v["kind"] == "vocab" and len(o) == 4
db.close()
srv.shutdown(); shutil.rmtree(tmp)
print("\nGrammar questions work in the game.")
