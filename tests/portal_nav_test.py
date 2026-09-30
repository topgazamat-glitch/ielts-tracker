"""The student's page in five sections — see the assertions for what it guarantees.

Run me with:  python3 run_tests.py                (all of them)
              python3 tests/portal_nav_test.py   (just this one)
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import tempfile, shutil, threading, time, re
import urllib.request
tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None); os.environ["TEACHER_PASSWORD"] = "testpw123"

import core, server
core.init_db(); db = core.connect()
now = core.iso(core.now())
g = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('214','AA',?)",
               (now,)).lastrowid
db.execute("INSERT INTO students (name, group_id, active, token, created_at)"
           " VALUES ('Shirin',?,1,'tok0000000000000001',?)", (g, now))
db.commit(); db.close()
srv = server.Server(("127.0.0.1", 8838), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start(); time.sleep(0.4)
B = "http://127.0.0.1:8838/s/tok0000000000000001"
def get(tab):
    return urllib.request.urlopen(B + "?tab=" + tab, timeout=30).read().decode("utf-8")

print("1. FIVE SECTIONS, NOT TEN TABS")
pg = get("home")
bar = re.search(r'<nav class="pnav"[^>]*>(.*?)</nav>', pg, re.S).group(1)
labels = re.findall(r"<span>([^<]+)</span>", bar)
print("   the bar:", labels)
assert labels == ["Homework", "Learn", "Play", "Progress", "Me"]
print("   each with an icon:", bar.count("<svg") == 5)
assert bar.count("<svg") == 5
print("   Homework is lit on the home tab:", 'class="on" href="' in bar and bar.index('class="on"') < bar.index("Learn"))
assert bar.index('class="on"') < bar.index("Learn")
print("   its own pages across the top: Send · Writing:", 'class="toptabs"' in pg and ">Send<" in pg and ">Writing<" in pg)
assert 'class="toptabs"' in pg and ">Send<" in pg and ">Writing<" in pg
print("   the old ten-tab strip is gone:", pg.count('class="tab') <= 4)
assert pg.count('class="tab') <= 4          # the strip plus Send · Writing · Feedback

print("\n2. EVERY OLD ADDRESS STILL LANDS IN THE RIGHT SECTION")
where = {"write": "Homework", "feedback": "Homework", "materials": "Learn", "handouts": "Learn", "tests": "Learn",
         "play": "Play", "battle": "Play", "progress": "Progress", "class": "Progress",
         "goal": "Progress", "profile": "Me"}
for tab, section in where.items():
    pg = get(tab)
    bar = re.search(r'<nav class="pnav"[^>]*>(.*?)</nav>', pg, re.S).group(1)
    lit = re.search(r'<a class="on" href="[^"]*">.*?<span>([^<]+)</span>', bar, re.S).group(1)
    print("   %-9s -> %-9s %s" % (tab, lit, "ok" if lit == section else "WRONG"))
    assert lit == section
pg = get("handouts")
strip = re.search(r'<nav class="toptabs"[^>]*>(.*?)</nav>', pg, re.S).group(1)
lit = re.search(r'<a href="([^"]*)" class="on"', strip)
print("   inside Learn the pages across the top are Materials · Handouts · Tests, with Handouts lit:",
      re.findall(r">([^<]+)</a>", strip) == ["Materials", "Handouts", "Tests"]
      and lit is not None and lit.group(1).endswith("tab=handouts"))
assert re.findall(r">([^<]+)</a>", strip) == ["Materials", "Handouts", "Tests"]
assert lit is not None and lit.group(1).endswith("tab=handouts")
pg = get("profile")
print("   a one-page section has no pages across the top:", 'class="toptabs"' not in pg)
assert 'class="toptabs"' not in pg

print("\n3. THE SAME FRAME AS THE TEACHER'S")
print("   the rail, with the student's name at its foot:", '<aside class="side"' in pg and "side-who" in pg
      and "Shirin" in pg.split('class="side-foot"')[1][:600])
assert '<aside class="side"' in pg and "Shirin" in pg.split('class="side-foot"')[1][:600]
css = open(os.path.join(ROOT, "static", "style.css")).read()
print("   the bar sits at the bottom on a phone:", "position: fixed; left: 0; right: 0; bottom: 0" in css.split(".pnav {", 2)[-1][:600])
assert ".pnav" in css and "safe-area-inset-bottom" in css

srv.shutdown(); shutil.rmtree(tmp)
print("\nA place with five rooms, not a corridor of ten doors.")
