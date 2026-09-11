"""Http — see the assertions for what it guarantees.

Run me with:  python3 run_tests.py            (all of them)
              python3 tests/http_test.py   (just this one)
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
FIXTURES = os.path.join(ROOT, "tests", "fixtures")

import tempfile, shutil, threading, urllib.request, urllib.error, time
tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None)

import core, server
core.init_db(); db = core.connect(); cfg = core.load_config()
today = core.local_day(core.now(), cfg)
blob = b"ID3\x03\x00\x00\x00\x00\x00\x00" + (b"\xff\xfb\x90\x00" + b"\x00" * 400) * 200
core.save_song(db, today, "day.mp3", blob, "Lovely Day", "Bill Withers")
db.close()

srv = server.Server(("127.0.0.1", 8799), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
time.sleep(0.4)
base = "http://127.0.0.1:8799"

def hit(path, headers=None):
    req = urllib.request.Request(base + path, headers=headers or {})
    try:
        r = urllib.request.urlopen(req)
        return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()

print("A logged-OUT visitor, exactly like a student:")
c, h, b = hit("/song")
print("  GET /song            -> %s  %s  %s bytes" % (c, h.get("Content-Type"), len(b)))
assert c == 200 and b == blob, (c, len(b))
c, h, b = hit("/song", {"Range": "bytes=0-999"})
print("  GET /song Range      -> %s  %s  %d bytes" % (c, h.get("Content-Range"), len(b)))
assert c == 206 and len(b) == 1000
c, h, b = hit("/song/" + today)
print("  GET /song/%s -> %s  %d bytes" % (today, c, len(b)))
assert c == 200
c, h, b = hit("/song/2001-01-01")
print("  GET a day with none  -> %s (404 expected)" % c)
assert c == 404
c, h, b = hit("/music")
print("  GET /music (teacher) -> %s (redirect to login expected)" % c)
assert b"password" in b.lower() or b"sign in" in b.lower(), "/music must demand a login"

print("\nA student portal page:")
db = core.connect()
g = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('T','TT',?)",
               (core.iso(core.now()),)).lastrowid
db.execute("INSERT INTO students (name, group_id, active, token, created_at)"
           " VALUES ('Ali',?,1,'stutoken_abcdefghijklmnop',?)", (g, core.iso(core.now()))); db.commit(); db.close()
c, h, b = hit("/s/stutoken_abcdefghijklmnop")
page = b.decode("utf-8", "replace")
print("  GET /s/stutoken_abcdefghijklmnop      -> %s, %d bytes" % (c, len(b)))
print("  declares the song:", "window.SONG" in page)
print("  names it on screen:", 'id="songname"' in page)
print("  loads the player:", "/static/music.js" in page)
assert c == 200 and "window.SONG" in page and "/static/music.js" in page
import re
print("  ", re.search(r"window\.SONG=\{[^}]*\}", page).group(0))
srv.shutdown(); shutil.rmtree(tmp)
print("\nServed correctly to a visitor with no login.")
