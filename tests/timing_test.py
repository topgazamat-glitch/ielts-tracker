"""The teacher sets the clock from the test page.

Run me with:  python3 run_tests.py timing
              python3 tests/timing_test.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import tempfile, threading, urllib.request, urllib.parse, time, http.cookiejar
tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None)

import core, server
core.init_db(); db = core.connect(); cfg = core.load_config()
tid = core.load_test(db, {
    "level": "Elementary", "number": 1, "title": "A mock",
    "layout": '<p>1 <span data-mcq="1"></span></p>',
    "questions": [{"num": 1, "kind": "mcq", "prompt": "One", "answer": "A",
                   "options": [{"letter": "A", "text": "yes"},
                               {"letter": "B", "text": "no"}]}]})
db.commit(); db.close()

srv = server.Server(("127.0.0.1", 8813), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
time.sleep(0.4)
base = "http://127.0.0.1:8813"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(base + "/login",
        urllib.parse.urlencode({"password": cfg["teacher_password"]}).encode())

def timing(**kw):
    op.open(base + "/tests/%d/timing" % tid,
            urllib.parse.urlencode(kw).encode())
    db = core.connect()
    r = db.execute("SELECT minutes, strict FROM dtests WHERE id=?", (tid,)).fetchone()
    db.close()
    return r["minutes"], r["strict"]

page = op.open(base + "/tests/%d" % tid).read().decode()
assert 'action="/tests/%d/timing"' % tid in page, "no clock control on the page"
print("the test page offers a clock control")

print("  set 50 minutes, strict     ->", timing(minutes="50", strict="1"))
assert timing(minutes="50", strict="1") == (50, 1)

print("  set 40 minutes, not strict ->", timing(minutes="40", strict="0"))
assert timing(minutes="40", strict="0") == (40, 0)

print("  cleared                    ->", timing(minutes="", strict="0"))
assert timing(minutes="", strict="0") == (None, 0)

print("  nonsense is refused        ->", timing(minutes="900", strict="0"),
      timing(minutes="abc", strict="0"))
assert timing(minutes="900", strict="0") == (None, 0)
assert timing(minutes="abc", strict="0") == (None, 0)

# what the student's page then carries
db = core.connect()
db.execute("UPDATE dtests SET minutes=45, strict=1, published=1 WHERE id=?", (tid,))
db.commit(); db.close()
page = op.open(base + "/tests/%d" % tid).read().decode()
assert 'value="45"' in page, "the page does not show the time it kept"
print("the page shows back the 45 minutes it kept")

srv.shutdown()
print("PASS  the clock is the teacher's to set")
