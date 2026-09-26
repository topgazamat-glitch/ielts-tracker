"""Insights — the cycle read back. See the assertions for what it guarantees.

Run me with:  python3 run_tests.py              (all of them)
              python3 tests/insights_test.py   (just this one)
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import tempfile, shutil, threading, time, re, http.cookiejar
import urllib.request, urllib.parse
tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None); os.environ["TEACHER_PASSWORD"] = "testpw123"

import core, server
core.init_db(); db = core.connect()
n = core.seed_demo(db)                 # the invented term: habits, tests, six leavers
db.commit()
g = db.execute("SELECT id FROM groups").fetchone()["id"]

print("1. THE NUMBERS BEHIND THE PAGE")
pts = core.cycle_points(db)
print("   students in the cycle:", len(pts), "(seeded %d)" % n)
assert len(pts) == n
rows = {r["key"]: r for r in core.left_vs_stayed(pts)}
hw = rows["completion"]
print("   homework done — stayed %s%%, left %s%%" % (hw["stayed"], hw["left"]))
assert hw["stayed"] > hw["left"], "the demo's leavers are its weakest homework habits"
room = rows["participation"]
print("   in the classroom — stayed %s, left %s" % (room["stayed"], room["left"]))
assert room["stayed"] > room["left"]
print("   the homework gap is more than chance:", hw["test"]["verdict"])
assert hw["test"]["verdict"] == "clear"
drivers = core.exam_drivers(pts)
print("   what moves with the exam, strongest first:",
      ", ".join("%s %s" % (d["label"], d["test"]["r"]) for d in drivers[:3]))
assert drivers[0]["test"]["verdict"] == "clear"
assert drivers[0]["key"] != "exam"
lines = core.cycle_findings(pts, core.retention(db))
print("   findings in sentences:", len(lines))
for s in lines:
    print("     -", s)
assert any("still here" in s for s in lines)
assert any("Homework done" in s or "Homework mark" in s for s in lines)

print("\n2. NOTHING IS SAID WITHOUT THE NUMBERS TO BACK IT")
few = core.cycle_findings(pts[:3], {"rate": None, "rate_ours": None, "here": 0, "left": 0})
print("   three students give one line:", len(few) == 1 and "Not enough" in few[0])
assert len(few) == 1 and "Not enough" in few[0]
empty = core.left_vs_stayed([])
print("   an empty school compares nothing:", all(r["stayed"] is None for r in empty))
assert all(r["stayed"] is None and r["left"] is None for r in empty)
db.close()

print("\n3. THE PAGE")
srv = server.Server(("127.0.0.1", 8834), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start(); time.sleep(0.4)
B = "http://127.0.0.1:8834"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(B + "/login", urllib.parse.urlencode({"password": "testpw123"}).encode()).read()
def get(u):
    r = op.open(B + u); return r.geturl()[len(B):], r.read().decode("utf-8")
where, pg = get("/insights")
print("   two donuts:", pg.count('class="donut"') == 2)
assert pg.count('class="donut"') == 2
print("   slices carry what they are:",
      'class="slice kept"' in pg and 'class="slice ours"' in pg)
assert 'class="slice kept"' in pg and 'class="slice ours"' in pg
print("   the reasons donut has slices:", pg.count('class="slice ') >= 5)
assert pg.count('class="slice ') >= 5
print("   stayed-against-left rows:", pg.count('class="row"') >= 5)
assert 'class="line stayed"' in pg and 'class="line left"' in pg
print("   the gap is named:", "a real gap" in pg)
assert "a real gap" in pg
print("   exam drivers drawn:", 'class="drivers"' in pg and 'class="r' in pg)
assert 'class="drivers"' in pg
print("   scatters with a finding:", pg.count("<svg") >= 4 and "There is something here" in pg)
assert pg.count("<svg") >= 4 and "There is something here" in pg
print("   findings on the page:", '<ol class="findings">' in pg)
assert '<ol class="findings">' in pg
print("   swappable (no inline script):",
      "<script" not in re.search(r"<main[^>]*>(.*)</main>", pg, re.S).group(1))
assert "<script" not in re.search(r"<main[^>]*>(.*)</main>", pg, re.S).group(1)

where, one = get(f"/insights?group={g}")
print("   one class filters:", "Demo 214" in one and 'class="tab on"' in one)
assert "Demo 214" in one
where, old = get(f"/records?v=charts&group={g}")
print("   the old charts address lands here:", where.startswith("/insights"))
assert where.startswith("/insights")
print("   Insights sits in the nav with KPI:",
      'href="/insights"' in pg and 'href="/kpi"' in pg)
assert 'href="/insights"' in pg and 'href="/kpi"' in pg

srv.shutdown(); shutil.rmtree(tmp)
print("\nThe cycle, read back and said out loud.")
