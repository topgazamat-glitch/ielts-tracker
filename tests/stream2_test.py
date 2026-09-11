"""Stream2 — see the assertions for what it guarantees.

Run me with:  python3 run_tests.py            (all of them)
              python3 tests/stream2_test.py   (just this one)
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
FIXTURES = os.path.join(ROOT, "tests", "fixtures")

import tempfile, shutil, threading, time, urllib.request, urllib.error, resource
tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None)

import core, server
core.init_db(); db = core.connect(); cfg = core.load_config()
today = core.local_day(core.now(), cfg)
blob = os.urandom(5431378)                       # the real song's size
core.save_song(db, today, "day.mp3", blob, "Test", None); db.close()
srv = server.Server(("127.0.0.1", 8810), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start(); time.sleep(0.4)
B = "http://127.0.0.1:8810/song"

def get(headers=None, method="GET"):
    r = urllib.request.Request(B, headers=headers or {}, method=method)
    try:
        x = urllib.request.urlopen(r); return x.status, dict(x.headers), x.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()

print("What a player asks for first: the open-ended range")
c, h, b = get({"Range": "bytes=0-"})
print("  %s  %s  -> %d bytes in ONE response" % (c, h.get("Content-Range"), len(b)))
assert c == 206 and len(b) == len(blob) and b == blob, "must send the whole track"
print("  the player never has to come back mid-song.")

print("\nPlain GET")
c, h, b = get()
print("  %s  %d bytes  cache: %s" % (c, len(b), h.get("Cache-Control")))
assert c == 200 and b == blob

print("\nHEAD")
c, h, b = get(method="HEAD")
print("  %s  length=%s  body=%d" % (c, h.get("Content-Length"), len(b)))
assert c == 200 and h.get("Content-Length") == str(len(blob)) and len(b) == 0

print("\nSeeking (a player resuming where it left off)")
c, h, b = get({"Range": "bytes=3000000-"})
print("  %s  %s  %d bytes" % (c, h.get("Content-Range"), len(b)))
assert c == 206 and b == blob[3000000:]
c, h, b = get({"Range": "bytes=100-199"})
assert c == 206 and b == blob[100:200]
print("  exact slice correct")
print("  past the end ->", get({"Range": "bytes=99999999-"})[0])
assert get({"Range": "bytes=99999999-"})[0] == 416

print("\nMemory while serving the whole file ten times over")
before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
for _ in range(10):
    get({"Range": "bytes=0-"})
after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
unit = 1024.0 * 1024 if sys.platform == "darwin" else 1024.0
print("  peak memory grew by %.1f MB while sending %.1f MB"
      % ((after - before) / unit, 10 * len(blob) / 1048576.0))
assert (after - before) / unit < 8, "streaming should not buffer whole files"
srv.shutdown(); shutil.rmtree(tmp)
print("\nWhole track, one response, flat memory.")
