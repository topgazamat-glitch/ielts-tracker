"""Auto — see the assertions for what it guarantees.

Run me with:  python3 run_tests.py            (all of them)
              python3 tests/auto_test.py   (just this one)
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
wl = db.execute("INSERT INTO word_lists (title, active, kind, created_at)"
                " VALUES ('G',1,'grammar',?)", (core.iso(core.now()),)).lastrowid
for i in range(6):
    db.execute("INSERT INTO words (list_id, term, translation, options, ord)"
               " VALUES (?,?,?,?,?)",
               (wl, "Q%d ____ ?" % i, "right%d" % i,
                json.dumps(["w1", "w2", "w3"]), i))
db.commit()
game = core.make_game(db, g, wl, q_count=4, seconds=20)
gid = game["id"] if isinstance(game, dict) else game
db.close()

def state():
    db = core.connect()
    r = db.execute("SELECT state, q_index FROM games WHERE id=?", (gid,)).fetchone()
    db.close(); return r["state"], r["q_index"]

print("1. THE GUARD: a stale press cannot skip a question")
print("   start:", state())
core.connect().close()
db = core.connect(); core.advance_game(db, gid, "lobby", -1); db.close()
print("   after Start ->", state())
assert state() == ("question", 0)
# the same press arriving twice, both claiming to come from the lobby
db = core.connect(); core.advance_game(db, gid, "lobby", -1); db.close()
print("   the same press again ->", state(), "(must not move)")
assert state() == ("question", 0)
# a timer firing that thinks it is still on question 0, after a manual press
db = core.connect(); core.advance_game(db, gid, "question", 0); db.close()
print("   timer fires  ->", state())
db = core.connect(); core.advance_game(db, gid, "question", 0); db.close()
print("   timer again  ->", state(), "(must not move)")
assert state() == ("reveal", 0)
db = core.connect(); core.advance_game(db, gid, "reveal", 0); db.close()
print("   reveal ends  ->", state())
assert state() == ("question", 1)

print("\n2. AN UNGUARDED CALL STILL WORKS (the old button)")
db = core.connect(); core.advance_game(db, gid); db.close()
print("   plain advance ->", state())
assert state() == ("reveal", 1)

print("\n3. RUNNING TO THE END")
for _ in range(10):
    st, _i = state()
    if st == "done":
        break
    db = core.connect(); core.advance_game(db, gid); db.close()
print("   final:", state())
assert state()[0] == "done"

print("\n4. THE BOARD PAGE CARRIES THE AUTO CONTROLS")
srv = server.Server(("127.0.0.1", 8831), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start(); time.sleep(0.4)
B = "http://127.0.0.1:8831"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(B + "/login", urllib.parse.urlencode({"password": "testpw123"}).encode()).read()
page = op.open(B + "/play/%d" % gid).read().decode("utf-8")
for what in ("Auto: on", "toggleAuto", "everyone answered", "next question in",
             "state=' + encodeURIComponent",
             'id="showfor"', 'id="minplayers"', "setShowFor", "setMin",
             "starting in", "waiting for", "loadPrefs()", "settleFor"):
    print("   %-28s %s" % (what[:28], what in page))
    assert what in page

print("\n5. THE SERVER IGNORES A STALE POST")
db = core.connect()
g2 = core.make_game(db, g, wl, q_count=4, seconds=20)
g2 = g2["id"] if isinstance(g2, dict) else g2
db.close()
op.open(B + "/play/%d/next" % g2, b"state=lobby&from=-1").read()
db = core.connect(); a = db.execute("SELECT state,q_index FROM games WHERE id=?", (g2,)).fetchone(); db.close()
print("   after one POST:", a["state"], a["q_index"])
op.open(B + "/play/%d/next" % g2, b"state=lobby&from=-1").read()
db = core.connect(); b = db.execute("SELECT state,q_index FROM games WHERE id=?", (g2,)).fetchone(); db.close()
print("   after the same POST again:", b["state"], b["q_index"], "(unchanged)")
assert (a["state"], a["q_index"]) == (b["state"], b["q_index"])
srv.shutdown(); shutil.rmtree(tmp)
print("\nAuto-advance is safe.")
