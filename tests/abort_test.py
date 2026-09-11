"""Abort — see the assertions for what it guarantees.

Run me with:  python3 run_tests.py            (all of them)
              python3 tests/abort_test.py   (just this one)
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
FIXTURES = os.path.join(ROOT, "tests", "fixtures")

import tempfile, shutil, threading, socket, time, io, contextlib
tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None)

import core, server
core.init_db(); db = core.connect(); cfg = core.load_config()
today = core.local_day(core.now(), cfg)
blob = os.urandom(3465716)                       # same size as the real song
core.save_song(db, today, "day.mp3", blob, "Test", None)
db.close()

srv = server.Server(("127.0.0.1", 8801), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
time.sleep(0.4)

err = io.StringIO()
def abort_after(nbytes, label):
    s = socket.create_connection(("127.0.0.1", 8801), timeout=10)
    s.sendall(b"GET /song HTTP/1.1\r\nHost: x\r\nRange: bytes=0-\r\n\r\n")
    got = 0
    while got < nbytes:
        d = s.recv(4096)
        if not d: break
        got += len(d)
    s.close()                                     # what an <audio> element does
    print("  %-28s read %7d bytes then hung up" % (label, got))

with contextlib.redirect_stderr(err):
    print("Client aborts mid-download, the way a media element does:")
    for n in (8192, 65536, 200000):
        abort_after(n, "abort after ~%d B" % n)
    time.sleep(0.8)

log = err.getvalue()
bad = [l for l in log.splitlines() if "Error" in l or "error" in l]
print("\nServer-side exceptions raised: %d" % len(bad))
for l in bad[:6]:
    print("   ", l.strip())
if "BrokenPipeError" in log or "ConnectionReset" in log:
    print("\n>>> the handler thread dies on every aborted range request")
srv.shutdown(); shutil.rmtree(tmp)
