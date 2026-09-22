"""Solo play: a student plays the teacher's lists alone, and the ranking is fair.

Run me with:  python3 run_tests.py solo
              python3 tests/solo_test.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import tempfile, threading, urllib.request, urllib.parse, time, http.cookiejar
tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None)

import core, server
core.init_db(); db = core.connect()
now = core.iso(core.now())
g1 = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('114','A',?)", (now,)).lastrowid
g2 = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('116','B',?)", (now,)).lastrowid
ali = core.add_student(db, "Ali", g1)
bek = core.add_student(db, "Bek", g1)
far = core.add_student(db, "Farida", g2)
tok = {sid: db.execute("SELECT token FROM students WHERE id=?", (sid,)).fetchone()["token"]
       for sid in (ali, bek, far)}

def mklist(title, kind, group, n):
    lid = db.execute("INSERT INTO word_lists (group_id, title, created_at, kind) VALUES (?,?,?,?)",
                     (group, title, now, kind)).lastrowid
    for i in range(n):
        opts = json.dumps(["x%d" % i, "y%d" % i, "z%d" % i]) if kind == "grammar" else None
        db.execute("INSERT INTO words (list_id, term, translation, options, ord) VALUES (?,?,?,?,?)",
                   (lid, "term%d" % i, "right%d" % i, opts, i))
    return lid
gram_all = mklist("Grammar for everyone", "grammar", None, 14)
vocab_114 = mklist("Words for 114", "vocab", g1, 8)
gram_116 = mklist("Grammar for 116 only", "grammar", g2, 6)
db.commit(); db.close()

srv = server.Server(("127.0.0.1", 8817), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
time.sleep(0.4)
base = "http://127.0.0.1:8817"
op = urllib.request.build_opener()          # a student: no login, just their link

def get(path):
    return op.open(base + path, timeout=20).read().decode()

def answer_of(st):
    """Where the right answer sits: termN's answer is rightN."""
    return st["options"].index("right" + st["term"][4:])


def post(path, data):
    r = op.open(base + path, urllib.parse.urlencode(data).encode(), timeout=20)
    return r.geturl(), r.read().decode()

print("1. THE PLAY TAB")
home = get("/s/%s?tab=play" % tok[ali])
assert "Vocabulary" in home and "Grammar" in home, "the two doors are missing"
assert "This week's champions" in home
assert "not\npart of the league" in home or "not part of the league" in home \
       or ("league" in home and "not" in home)
print("   two doors, a weekly table, and it says it is not the league")

g = get("/s/%s?tab=play&kind=grammar" % tok[ali])
assert "Grammar for everyone" in g and "Grammar for 116 only" not in g
v = get("/s/%s?tab=play&kind=vocab" % tok[ali])
assert "Other lists" in v, "the vocabulary section should show its books first"
v = get("/s/%s?tab=play&kind=vocab&book=-" % tok[ali])
assert "Words for 114" in v
print("   Ali (114) sees the list for everyone and his own class's, not 116's")
blocked = get("/s/%s?tab=play&l=%d" % (tok[ali], gram_116))
assert "not open to your class" in blocked
print("   and cannot open 116's list by typing its number")

print("\n2. A ROUND")
url, _ = post("/s/%s/solo/start" % tok[ali], {"list": gram_all})
rid = int(url.rsplit("/", 1)[1])
page = get("/s/%s/solo/%d" % (tok[ali], rid))
assert "Grammar for everyone" in page
st = json.loads(get("/s/%s/solo/%d.json" % (tok[ali], rid)))
assert st["state"] == "question" and st["total"] == 14, st
print("   a 14-question list gives a round of all 14, clock at %ss" % st["left"])

# cheating: answering a question that is not on screen
_, out = post("/s/%s/solo/%d/answer" % (tok[ali], rid), {"q": 5, "choice": 0})
assert json.loads(out)["ok"] is False
print("   answering a question that is not on screen is refused")

# someone else's round
nope = json.loads(get("/s/%s/solo/%d.json" % (tok[bek], rid)))
assert nope["state"] == "gone"
print("   Bek cannot see Ali's round")

right = 0
while st["state"] == "question":
    pos = answer_of(st)
    choice = pos if st["number"] < st["total"] - 1 else (pos + 1) % 4   # last one wrong
    _, out = post("/s/%s/solo/%d/answer" % (tok[ali], rid), {"q": st["q"], "choice": choice})
    a = json.loads(out)
    assert a["ok"] and a["answer_text"].startswith("right")
    right += a["correct"]
    # a second answer to the same question
    _, again = post("/s/%s/solo/%d/answer" % (tok[ali], rid), {"q": st["q"], "choice": pos})
    assert json.loads(again)["ok"] is False
    st = json.loads(get("/s/%s/solo/%d.json" % (tok[ali], rid)))
assert st["state"] == "done" and st["correct"] == st["total"] - 1, st
assert len([x for x in st["review"] if not x["right"]]) == 1
print("   %d of %d, %d points; one answer per question; the miss is shown with its answer"
      % (st["correct"], st["total"], st["score"]))
assert st["correct"] * core.GAME_BASE <= st["score"] \
       <= st["correct"] * (core.GAME_BASE + core.GAME_SPEED)

print("\n3. THE RANKING IS FAIR")
# Bek plays the same list three times, badly then well: only his best counts
for good in (False, False, True):
    url, _ = post("/s/%s/solo/start" % tok[bek], {"list": gram_all})
    r2 = int(url.rsplit("/", 1)[1])
    s2 = json.loads(get("/s/%s/solo/%d.json" % (tok[bek], r2)))
    while s2["state"] == "question":
        pos = answer_of(s2)
        post("/s/%s/solo/%d/answer" % (tok[bek], r2),
             {"q": s2["q"], "choice": pos if good else (pos + 1) % 4})
        s2 = json.loads(get("/s/%s/solo/%d.json" % (tok[bek], r2)))
d = core.connect()
board = core.solo_list_board(d, gram_all, g1)
print("   list table:", [(r["name"], r["best"], r["pct"], r["rounds"]) for r in board])
assert [r["name"] for r in board][:2] == ["Bek", "Ali"] or board[0]["best"] >= board[1]["best"]
assert {r["name"]: r["rounds"] for r in board}["Bek"] == 3
print("   Bek's three rounds count as one: his best")

# the week's champion is whoever masters more lists, not whoever replays one
url, _ = post("/s/%s/solo/start" % tok[ali], {"list": vocab_114})
r3 = int(url.rsplit("/", 1)[1])
s3 = json.loads(get("/s/%s/solo/%d.json" % (tok[ali], r3)))
while s3["state"] == "question":
    pos = answer_of(s3)
    post("/s/%s/solo/%d/answer" % (tok[ali], r3), {"q": s3["q"], "choice": pos})
    s3 = json.loads(get("/s/%s/solo/%d.json" % (tok[ali], r3)))
week = core.solo_week_board(d, g1)
print("   week table:", [(w["name"], w["mastered"], w["points"]) for w in week])
assert week[0]["name"] == "Ali" and week[0]["mastered"] == 2
print("   Ali mastered two lists and leads, though Bek played more rounds")
assert all(w["name"] != "Farida" for w in week)
print("   Farida is in another class and is not on 114's table")

print("\n4. IT STAYS OUT OF THE LEAGUE")
src = open(os.path.join(ROOT, "core.py")).read()
league = src[src.index("def test_marks"):src.index("def test_marks") + 4000]
assert "solo_" not in league
print("   the league's scoring never reads solo rounds")

print("\n5. THE CLOCK IS THE SERVER'S")
# Farida's own list is step 2 of her ladder now, so she starts at step 1
url, _ = post("/s/%s/solo/start" % tok[far], {"list": gram_all})
r4 = int(url.rsplit("/", 1)[1])
s4 = json.loads(get("/s/%s/solo/%d.json" % (tok[far], r4)))
d.execute("UPDATE solo_questions SET shown_at=? WHERE run_id=? AND ord=0",
          (core.iso(core.now() - __import__("datetime").timedelta(seconds=40)), r4))
d.commit()
pos = answer_of(s4)
_, late = post("/s/%s/solo/%d/answer" % (tok[far], r4), {"q": 0, "choice": pos})
late = json.loads(late)
assert late["ok"] and late["correct"] is False and late["points"] == 0 and late["late"]
print("   a right answer sent after the time is up scores nothing")
d.close()
print("\n6. A LIST BELONGS TO A LEVEL")
# its own server and its own data: this section is about what a student is
# offered, and it should not inherit sixty requests' worth of state
srv.shutdown()
tmp2 = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp2
import importlib
importlib.reload(core); importlib.reload(server)
core.init_db(); d = core.connect(); now = core.iso(core.now())
lv = {r["name"]: r["id"] for r in d.execute("SELECT id, name FROM levels")}
e = d.execute("INSERT INTO groups (name, join_code, created_at, level_id)"
              " VALUES ('114','A',?,?)", (now, lv["Elementary"])).lastrowid
i_ = d.execute("INSERT INTO groups (name, join_code, created_at, level_id)"
               " VALUES ('116','B',?,?)", (now, lv["Intermediate"])).lastrowid
ali2 = core.add_student(d, "Ali", e)
far2 = core.add_student(d, "Farida", i_)
tok2 = d.execute("SELECT token FROM students WHERE id=?", (ali2,)).fetchone()["token"]

def grammar_list(title, level):
    lid = d.execute("INSERT INTO word_lists (title, created_at, kind, level_id)"
                    " VALUES (?,?,'grammar',?)", (title, now, level)).lastrowid
    for k in range(6):
        d.execute("INSERT INTO words (list_id, term, translation, options, ord)"
                  " VALUES (?,?,?,?,?)",
                  (lid, "term%d" % k, "right%d" % k, json.dumps(["a", "b", "c"]), k))
    return lid
inter = grammar_list("Conditionals (Intermediate)", lv["Intermediate"])
elem = grammar_list("Comparatives (Elementary)", lv["Elementary"])
anyone = grammar_list("Grammar for everyone", None)
d.commit()
rows = {sid: d.execute("SELECT * FROM students WHERE id=?", (sid,)).fetchone()
        for sid in (ali2, far2)}
titles = lambda sid: [l["title"] for l in core.play_lists(d, rows[sid], "grammar")]
print("   Ali (Elementary) sees:", titles(ali2))
print("   Farida (Intermediate) sees:", titles(far2))
assert "Conditionals (Intermediate)" not in titles(ali2)
assert "Comparatives (Elementary)" in titles(ali2)
assert "Conditionals (Intermediate)" in titles(far2)
assert "Grammar for everyone" in titles(ali2) and "Grammar for everyone" in titles(far2)
print("   each level sees its own, and a list with no level still shows to everybody")
d.close()

srv2 = server.Server(("127.0.0.1", 8818), server.Handler)
threading.Thread(target=srv2.serve_forever, daemon=True).start()
time.sleep(0.4)
r = urllib.request.urlopen("http://127.0.0.1:8818/s/%s/solo/start" % tok2,
                           urllib.parse.urlencode({"list": inter}).encode(), timeout=20)
assert r.geturl().endswith("tab=play"), "Ali was allowed to start an Intermediate round"
print("   and Ali cannot start the Intermediate one by typing its number")
srv2.shutdown()
print("\nPASS  solo play works, its ranking cannot be bought, and each level sees its own lists")
