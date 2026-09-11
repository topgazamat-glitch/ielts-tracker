"""Revert — see the assertions for what it guarantees.

Run me with:  python3 run_tests.py            (all of them)
              python3 tests/revert_test.py   (just this one)
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
FIXTURES = os.path.join(ROOT, "tests", "fixtures")

import tempfile, shutil, threading, time, json, urllib.request
tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None); os.environ["TEACHER_PASSWORD"] = "testpw123"

import core, server, bot
core.init_db(); db = core.connect()
core.meta_set(db, "site_url", "https://example.up.railway.app")
g = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('T','TT',?)",
               (core.iso(core.now()),)).lastrowid
db.execute("INSERT INTO students (name, group_id, active, token, telegram_id, lang,"
           " created_at) VALUES ('Ali',?,1,'tok0000000000000000',555,'en',?)",
           (g, core.iso(core.now()))); db.commit()
st = db.execute("SELECT * FROM students WHERE name='Ali'").fetchone()

sent = []
bot.call = lambda token, method, **kw: (sent.append((method, kw)), {"ok": True})[1]

print("1. The page message is a plain link again")
bot.send_my_page(db, "TOK", st)
for m, kw in sent:
    print("   %s  reply_markup=%s" % (m, json.dumps(kw.get("reply_markup"))))
assert not any(m == "setChatMenuButton" for m, _ in sent), "must not set a menu button"
assert "web_app" not in json.dumps(sent), "no web_app buttons anywhere"
txt = [kw for m, kw in sent if m == "sendMessage"][0]["text"]
print("   text mentions the home screen again:", "home screen" in txt)

print("\n2. A student who was given a button gets it taken back")
core.meta_set(db, "menu:555", core.iso(core.now()))
sent.clear()
bot.clear_menu_button(db, "TOK", st)
print("   api calls:", [(m, kw.get("menu_button")) for m, kw in sent])
assert sent and sent[0][1]["menu_button"] == {"type": "default"}
assert not [m for m, _ in sent if m == "sendMessage"], "must send no message"
print("   flag cleared:", not core.meta_get(db, "menu:555"))

print("\n3. It then costs nothing, forever")
sent.clear()
for _ in range(5):
    bot.clear_menu_button(db, "TOK", st)
print("   five more passes ->", len(sent), "api calls")
assert len(sent) == 0

print("\n4. A student who never got one is untouched")
core.meta_set(db, "site_url", "https://example.up.railway.app")
sent.clear()
bot.clear_menu_button(db, "TOK", st)
assert len(sent) == 0
print("   no calls. good.")

db.close()
srv = server.Server(("127.0.0.1", 8809), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start(); time.sleep(0.4)
B = "http://127.0.0.1:8809"
r = urllib.request.urlopen(B + "/s/tok0000000000000000")
h = dict(r.headers); page = r.read().decode("utf-8")
print("\n5. The web page is back to how it was")
print("   X-Frame-Options: %s (DENY everywhere again)" % h.get("X-Frame-Options"))
print("   telegram scripts gone:", "telegram" not in page.lower())
print("   nav + music still there:", "/static/nav.js" in page and "/static/music.js" in page)
assert h.get("X-Frame-Options") == "DENY" and "telegram" not in page.lower()
assert "/static/nav.js" in page and "/static/music.js" in page
print("   telegram.js is gone from the server:",
      urllib.request.urlopen(B + "/static/telegram.js").status if 0 else "404 expected")
try:
    urllib.request.urlopen(B + "/static/telegram.js"); print("   STILL SERVED - bad")
except Exception as e:
    print("   /static/telegram.js ->", e.code)
srv.shutdown(); shutil.rmtree(tmp)
print("\nFully reverted.")
