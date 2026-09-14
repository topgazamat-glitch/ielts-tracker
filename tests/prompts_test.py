"""Prompts — the site suggests a writing question instead of you inventing one.

Run me with:  python3 run_tests.py prompts
"""
import http.cookiejar
import json
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
core.init_db()
srv = server.Server(("127.0.0.1", 8881), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start(); time.sleep(0.4)
B = "http://127.0.0.1:8881"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(B + "/login", urllib.parse.urlencode({"password": "pw"}).encode()).read()
def get(u): return op.open(B + u).read().decode()
def post(u, d): return op.open(B + u, urllib.parse.urlencode(d, doseq=True).encode()).read().decode()

print("1. THE BANK ARRIVES FILLED")
db = core.connect()
n = db.execute("SELECT COUNT(*) c FROM prompts").fetchone()["c"]
by = db.execute("SELECT level, COUNT(*) c FROM prompts GROUP BY level ORDER BY level").fetchall()
print("   %d questions:" % n)
for r in by:
    print("      %-18s %d" % (r["level"], r["c"]))
assert n >= 40
db.close()

print("\n2. ASKING FOR ONE")
d = json.loads(get("/prompts/suggest?level=Intermediate&kind=opinion"))
print("   ok:", d["ok"])
print("   question:", d["text"][:64] + "...")
print("   it carries the level's length and timing: %s words, %s minutes"
      % (d["min_words"], d["minutes"]))
assert d["ok"] and len(d["text"]) > 40 and d["min_words"]

print("\n3. IT DOES NOT REPEAT ITSELF")
seen = set()
for _ in range(8):
    seen.add(json.loads(get("/prompts/suggest?level=Intermediate&kind=opinion"))["text"])
print("   eight requests gave %d different questions" % len(seen))
assert len(seen) >= 3

print("\n4. ASKING FOR SOMETHING THAT IS NOT THERE")
d = json.loads(get("/prompts/suggest?level=Beginner&kind=task2"))
print("   ok:", d["ok"], "|", d.get("why"))
assert not d["ok"]

print("\n5. THE BUTTON IS ON THE ASSIGNMENT FORM")
a = get("/assignments")
for what in ('id="sug_level"', 'id="sug_kind"', 'id="suggest"', "/prompts"):
    print("   %-18s %s" % (what, what in a))
    assert what in a

print("\n6. THE TEACHER CAN ADD THEIR OWN")
post("/prompts/new", {"level": "Elementary", "kind": "email",
                      "text": "Write an email inviting a friend to your birthday.",
                      "min_words": "80", "minutes": "25"})
page = get("/prompts?level=Elementary")
print("   listed:", "inviting a friend to your birthday" in page)
print("   marked as yours:", "yours" in page)
assert "inviting a friend to your birthday" in page
db = core.connect()
mine = db.execute("SELECT * FROM prompts WHERE mine=1").fetchone()
print("   stored with %s words, %s minutes" % (mine["min_words"], mine["minutes"]))
assert mine["min_words"] == 80
db.close()

print("\n7. AND REMOVE ONE")
post("/prompts/delete", {"id": mine["id"]})
print("   gone:", "inviting a friend to your birthday" not in get("/prompts?level=Elementary"))

print("\n8. SEEDING HAPPENS ONCE, NOT EVERY VISIT")
db = core.connect()
before = db.execute("SELECT COUNT(*) c FROM prompts").fetchone()["c"]
core.seed_prompts(db); core.seed_prompts(db)
after = db.execute("SELECT COUNT(*) c FROM prompts").fetchone()["c"]
print("   %d -> %d" % (before, after))
assert before == after
db.close()

print("\n9. THE COURSEBOOK'S OWN WRITING LESSONS")
u = json.loads(get("/prompts/units?level=Intermediate"))
print("   Intermediate units with a writing lesson:",
      [x["unit"] for x in u["units"]])
assert len(u["units"]) >= 8
print("   unit 6 is about:", next(x for x in u["units"] if x["unit"] == 6)["topic"])
print("   taught in:", next(x for x in u["units"] if x["unit"] == 6)["lesson"])
e = json.loads(get("/prompts/units?level=Elementary"))
print("   Elementary units:", [x["unit"] for x in e["units"]])
assert len(e["units"]) == 12

print("\n10. ASKING FOR ONE UNIT'S WRITING")
d = json.loads(get("/prompts/suggest?level=Intermediate&kind=coursebook&unit=6"))
print("   ", d["where"])
print("   ", d["text"])
assert d["ok"] and "review" in d["text"].lower() and "Unit 6" in d["where"]
d2 = json.loads(get("/prompts/suggest?level=Elementary&kind=coursebook&unit=4"))
print("   ", d2["where"], "->", d2["text"])
assert "Food" in d2["where"]

print("\n11. THE PICKER IS ON THE FORM")
a2 = get("/assignments")
print("   a unit dropdown:", 'id="sug_unit"' in a2)
assert 'id="sug_unit"' in a2

print("\n12. THE PAGE STAYS SWAPPABLE")
body = re.search(r"<main[^>]*>(.*)</main>", get("/prompts"), re.S).group(1)
print("   no inline script in main:", "<script" not in body)
assert "<script" not in body
srv.shutdown(); shutil.rmtree(tmp)
print("\nThe box is never empty.")
