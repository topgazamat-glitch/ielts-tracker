"""Game — see the assertions for what it guarantees.

Run me with:  python3 run_tests.py            (all of them)
              python3 tests/game_test.py   (just this one)
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
db.execute("INSERT INTO students (name, group_id, active, token, created_at)"
           " VALUES ('Ali',?,1,'tok0000000000000000',?)", (g, core.iso(core.now())))
wl = db.execute("INSERT INTO word_lists (group_id, title, active, created_at)"
                " VALUES (?,'Unit 1',1,?)", (g, core.iso(core.now()))).lastrowid
for w in ["abandon","ability","abolish","absorb","abstract","absurd"]:
    db.execute("INSERT INTO words (list_id, term, translation) VALUES (?,?,?)",
               (wl, w, "uz " + w))
db.commit()
game = core.make_game(db, g, wl)
gid = game["id"] if isinstance(game, dict) else game
db.close()
srv = server.Server(("127.0.0.1", 8807), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start(); time.sleep(0.4)
B = "http://127.0.0.1:8807"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(B + "/login", urllib.parse.urlencode({"password": "testpw123"}).encode()).read()

def check(label, url, opener):
    h = opener.open(url).read().decode("utf-8", "replace")
    m = re.search(r"<main[^>]*>(.*)</main>", h, re.S)
    body = m.group(1) if m else h
    inline = "<script" in body
    print("  %-22s inline script: %-5s -> %s" % (
        label, inline, "FULL RELOAD (protected)" if inline else "would be swapped"))
    return inline

print("Pages that run their own live code:")
a = check("teacher game board", B + "/play/%d" % gid, op)
b = check("student game screen", B + "/s/tok0000000000000000/game", urllib.request.build_opener())
assert a, "the game board MUST fall back to a full load"
assert b, "the student game screen MUST fall back to a full load"
print("\nBoth game screens are protected from swapping. Correct.")
srv.shutdown(); shutil.rmtree(tmp)
