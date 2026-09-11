"""Materials — see the assertions for what it guarantees.

Run me with:  python3 run_tests.py            (all of them)
              python3 tests/materials_test.py   (just this one)
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
FIXTURES = os.path.join(ROOT, "tests", "fixtures")

import tempfile, shutil, threading, time, re, json, http.cookiejar
import urllib.request, urllib.parse, html as htmlmod
tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None); os.environ["TEACHER_PASSWORD"] = "testpw123"

import core, server
core.init_db(); db = core.connect()
g = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('T','TT',?)",
               (core.iso(core.now()),)).lastrowid
db.execute("INSERT INTO students (name, group_id, active, token, created_at)"
           " VALUES ('Ali',?,1,'tok0000000000000000',?)", (g, core.iso(core.now())))
db.commit(); db.close()
srv = server.Server(("127.0.0.1", 8806), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start(); time.sleep(0.4)
B = "http://127.0.0.1:8806"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(B + "/login", urllib.parse.urlencode({"password": "testpw123"}).encode()).read()

page = op.open(B + "/materials").read().decode("utf-8")
m = re.search(r'id="coll"\s+data-sections="([^"]*)"', page)
print("data-sections attribute present:", bool(m))
data = json.loads(htmlmod.unescape(m.group(1)))
print("collections carried: %d -> %s" % (len(data), list(data)[:4]))
first = list(data)[0]
print("sections under %r: %s" % (first, data[first][:4]))
assert data and all(isinstance(v, list) for v in data.values())
print("both selects still rendered:", 'id="coll"' in page and 'id="sect"' in page)
print("no inline script left in main:",
      "<script" not in re.search(r"<main[^>]*>(.*)</main>", page, re.S).group(1))
print("materials.js is loaded by the shell:", "/static/materials.js" in page)
print("materials.js is served:", op.open(B + "/static/materials.js").status)

print("\nGame pages must NOT be swapped (they carry their own scripts):")
for path in ["/play"]:
    p = op.open(B + path).read().decode("utf-8")
    body = re.search(r"<main[^>]*>(.*)</main>", p, re.S).group(1)
    print("  %-8s inline script in main: %s -> %s" % (
        path, "<script" in body, "reloads (protected)" if "<script" in body else "swaps"))
srv.shutdown(); shutil.rmtree(tmp)
