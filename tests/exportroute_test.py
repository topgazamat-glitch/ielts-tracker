"""The Import page's "Download backup" hands back something importable.

Two functions were both called view_backup, so /backup.json served the raw
database file the Import page cannot read. This checks the route by what
comes out of it, not by which function it points at.

Run me with:  python3 run_tests.py exportroute
              python3 tests/exportroute_test.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import tempfile, threading, urllib.request, urllib.error, time, http.cookiejar
tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None)

import core, server
core.init_db(); db = core.connect(); cfg = core.load_config()
gid = db.execute("INSERT INTO groups (name, join_code, created_at)"
                 " VALUES (?,?,?)", ("114", "LX59FK",
                                     core.iso(core.now()))).lastrowid
db.commit()
core.add_student(db, "Dilnoza", gid)
db.close()

srv = server.Server(("127.0.0.1", 8812), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
time.sleep(0.4)
base = "http://127.0.0.1:8812"

jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(base + "/login",
        urllib.parse.urlencode({"password": cfg["teacher_password"]}).encode())

r = op.open(base + "/backup.json")
kind = r.headers.get("Content-Type", "")
raw = r.read()
print("GET /backup.json -> %s  %s bytes" % (kind, len(raw)))
assert "json" in kind, kind
assert not raw.startswith(b"SQLite format"), "that is the database, not an export"

data = json.loads(raw.decode("utf-8"))
print("  it carries:", ", ".join(sorted(data)[:8]))
assert "students" in data, sorted(data)
assert any(s["name"] == "Dilnoza" for s in data["students"])

srv.shutdown()
print("PASS  the Import page is handed a file it can read back")
