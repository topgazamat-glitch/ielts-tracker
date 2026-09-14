"""Marks — one tap a student, presets, and last lesson's marks carried over.

Run me with:  python3 run_tests.py marks
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
from datetime import timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None); os.environ["TEACHER_PASSWORD"] = "pw"
import core, server
core.init_db(); db = core.connect(); cfg = core.load_config()
g = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('114','A',?)",
               (core.iso(core.now()),)).lastrowid
ids = []
for n in ("Ali", "Bek", "Dilnoza"):
    ids.append(db.execute("INSERT INTO students (name, group_id, active, created_at)"
        " VALUES (?,?,1,?)", (n, g, core.iso(core.now()))).lastrowid)
yesterday = core.local_day(core.now() - timedelta(days=1), cfg)
today = core.local_day(core.now(), cfg)
for sid in ids:
    core.save_mark(db, sid, yesterday,
                   {"punctuality": 4, "behaviour": 5, "participation": 3}, None)
db.commit(); db.close()

srv = server.Server(("127.0.0.1", 8871), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start(); time.sleep(0.4)
B = "http://127.0.0.1:8871"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(B + "/login", urllib.parse.urlencode({"password": "pw"}).encode()).read()
def get(u): return op.open(B + u).read().decode("utf-8")
def post(u, d): return op.open(B + u, urllib.parse.urlencode(d, doseq=True).encode()).read().decode("utf-8")

page = get("/groups/%d?tab=marks" % g)
print("1. ONE TAP, NOT THREE DROPDOWNS")
pads = len(re.findall(r'class="mk" data-sid="\d+" data-v="[1-5]"', page))
print("   whole-student buttons on the page: %d  (3 students x 5)" % pads)
assert pads == 15
print("   no dropdowns left:", page.count('<select name="punctuality') == 0)
assert '<select name="punctuality' not in page

print("\n2. THE SHORTCUTS ARE THERE")
for what in ("Everyone 5", "Everyone 4", "Same as " + yesterday, "Clear", "split", "absent"):
    print("   %-22s %s" % (what, what in page))
    assert what in page

print("\n3. LAST LESSON TRAVELS WITH EACH ROW")
lasts = re.findall(r'data-last="([^"]*)"', page)
print("   rows carrying yesterday's marks:", lasts)
assert lasts == ["4,5,3"] * 3

print("\n4. SAVING STILL WORKS THE SAME WAY")
form = {"day": today, "day2": today}
for sid in ids:
    for f, v in zip(core.MARK_FIELDS, (5, 5, 5)):
        form["%s_%d" % (f, sid)] = v
form["note_%d" % ids[0]] = "spoke a lot today"
post("/groups/%d/marks" % g, form)
db = core.connect()
saved = core.marks_on(db, g, today)
print("   students marked today:", len(saved))
for sid in ids:
    r = saved[sid]
    assert (r["punctuality"], r["behaviour"], r["participation"]) == (5, 5, 5)
print("   all three fields stored per student: True")
print("   the note survived:", saved[ids[0]]["note"])
assert saved[ids[0]]["note"] == "spoke a lot today"
db.close()

print("\n5. A STUDENT CAN STILL BE MARKED UNEVENLY")
form = {"day": today, "day2": today}
form["punctuality_%d" % ids[1]] = 2
form["behaviour_%d" % ids[1]] = 5
form["participation_%d" % ids[1]] = 5
post("/groups/%d/marks" % g, form)
db = core.connect()
r = core.marks_on(db, g, today)[ids[1]]
print("   late but worked well:", (r["punctuality"], r["behaviour"], r["participation"]))
assert (r["punctuality"], r["behaviour"], r["participation"]) == (2, 5, 5)
db.close()

print("\n6. THE PAGE STAYS SWAPPABLE")
body = re.search(r"<main[^>]*>(.*)</main>", get("/groups/%d?tab=marks" % g), re.S).group(1)
print("   no inline script in main:", "<script" not in body)
assert "<script" not in body
srv.shutdown(); shutil.rmtree(tmp)
print("\nMarking a lesson is a few taps now.")
