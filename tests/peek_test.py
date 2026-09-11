"""Peek — a student's page opens beside the teacher's, not on top of it.

Run me with:  python3 run_tests.py peek
"""
import http.cookiejar
import os
import re
import shutil
import sys
import tempfile
import threading
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None); os.environ["TEACHER_PASSWORD"] = "pw"
import core, server
core.init_db(); db = core.connect()
g = db.execute("INSERT INTO groups (name, join_code, level_id, created_at)"
               " VALUES ('114','A',2,?)", (core.iso(core.now()),)).lastrowid
sid = db.execute("INSERT INTO students (name, group_id, active, created_at)"
                 " VALUES ('Ali',?,1,?)", (g, core.iso(core.now()))).lastrowid
tok = core.student_token(db, sid)
db.commit(); db.close()

srv = server.Server(("127.0.0.1", 8870), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start(); time.sleep(0.4)
B = "http://127.0.0.1:8870"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(B + "/login", urllib.parse.urlencode({"password": "pw"}).encode()).read()
def get(u): return op.open(B + u).read().decode("utf-8")

print("1. THE STUDENT'S RECORD")
page = get("/students/%d" % sid)
m = re.search(r'<a class="btnlink"[^>]*href="/s/([A-Za-z0-9_-]+)"[^>]*>Open their page</a>', page)
if not m:
    m = re.search(r'<a class="btnlink" target="_blank" rel="noopener"\s*href="/s/([A-Za-z0-9_-]+)">Open their page</a>', page)
print("   an Open button is offered:", bool(m))
assert 'Open their page' in page
link = re.search(r'class="btnlink"[^>]*>Open their page', page).group(0)
print("   it opens in its own window:", 'target="_blank"' in link)
print("   and cannot reach back into this one:", 'rel="noopener"' in link)
assert 'target="_blank"' in link and 'rel="noopener"' in link
print("   it points at the right student:", tok in page)
assert tok in page

print("\n2. THE ROSTER")
r = get("/roster")
peek = re.search(r'<a class="peek"[^>]*>', r)
print("   a peek arrow per student:", bool(peek))
print("   opens in its own window:", peek and 'target="_blank"' in peek.group(0))
assert peek and 'target="_blank"' in peek.group(0) and 'rel="noopener"' in peek.group(0)

print("\n3. THE SWAPPING NAVIGATION LEAVES THEM ALONE")
nav = open(os.path.join(ROOT, "static", "nav.js")).read()
print("   nav.js skips links with a target:", "a.target" in nav)
assert "a.target" in nav

print("\n4. THE PAGE IT OPENS REALLY IS THE STUDENT'S")
sp = urllib.request.urlopen(B + "/s/%s" % tok).read().decode("utf-8")
print("   reachable without signing in:", "Ali" in sp)
print("   and it is the student view, not the teacher's:", "/roster" not in sp)
assert "Ali" in sp and "/roster" not in sp
srv.shutdown(); shutil.rmtree(tmp)
print("\nA student's page opens beside the teacher's, not on top of it.")
