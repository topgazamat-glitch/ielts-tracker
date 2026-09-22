"""A word list can be renamed and moved to a class, and keeps its words.

Run me with:  python3 run_tests.py listrename
              python3 tests/listrename_test.py
"""
import json
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
db.commit(); db.close()

srv = server.Server(("127.0.0.1", 8816), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
time.sleep(0.4)
base = "http://127.0.0.1:8816"
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
op.open(base + "/login", urllib.parse.urlencode({"password": cfg["teacher_password"]}).encode())

r = op.open(base + "/vocab/new", urllib.parse.urlencode({
    "title": "Grammar review", "group_id": "", "kind": "grammar",
    "words": "She ___ to school. = goes | go | going | is go\n"
             "Look! It ___ . = is raining | rains | rained | raining"}).encode())
wid = int(r.geturl().rsplit("/", 1)[1])

page = op.open(base + "/vocab/%d" % wid).read().decode()
assert 'action="/vocab/%d/rename"' % wid in page, "no rename form on the list page"
print("the list page offers Rename")

op.open(base + "/vocab/%d/rename" % wid, urllib.parse.urlencode(
    {"title": "Grammar review (Elementary)", "group_id": str(gid)}).encode())
d = core.connect()
wl = d.execute("SELECT title, group_id FROM word_lists WHERE id=?", (wid,)).fetchone()
words = d.execute("SELECT term, translation, options FROM words WHERE list_id=? ORDER BY ord",
                  (wid,)).fetchall()
print("  renamed to %r, class %s" % (wl["title"], wl["group_id"]))
assert wl["title"] == "Grammar review (Elementary)" and wl["group_id"] == gid
assert len(words) == 2 and json.loads(words[0]["options"]) == ["go", "going", "is go"]
print("  both questions kept, with their own wrong answers")

op.open(base + "/vocab/%d/rename" % wid, urllib.parse.urlencode(
    {"title": "Grammar review (Elementary)", "group_id": ""}).encode())
wl = d.execute("SELECT group_id FROM word_lists WHERE id=?", (wid,)).fetchone()
assert wl["group_id"] is None
print("  and back to every class")

op.open(base + "/vocab/%d/rename" % wid, urllib.parse.urlencode(
    {"title": "   ", "group_id": ""}).encode())
wl = d.execute("SELECT title FROM word_lists WHERE id=?", (wid,)).fetchone()
assert wl["title"] == "Grammar review (Elementary)", "an empty title was accepted"
print("  an empty title is refused")
d.close()
srv.shutdown()
print("PASS  a list can be renamed and moved without losing a word")
