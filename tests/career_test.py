"""Play as a career: steps unlock only when the one before them is passed.

Run me with:  python3 run_tests.py career
              python3 tests/career_test.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import tempfile, threading, urllib.request, urllib.parse, time
tmp = tempfile.mkdtemp(); os.environ["DATA_DIR"] = tmp
os.environ.pop("TELEGRAM_TOKEN", None)

import core, server
core.init_db(); db = core.connect(); now = core.iso(core.now())
lv = {r["name"]: r["id"] for r in db.execute("SELECT id, name FROM levels")}
g = db.execute("INSERT INTO groups (name, join_code, created_at, level_id)"
               " VALUES ('214','A',?,?)", (now, lv["Pre-Intermediate"])).lastrowid
sid = core.add_student(db, "Aziz", g)
me = db.execute("SELECT * FROM students WHERE id=?", (sid,)).fetchone()
tok = me["token"]

def mklist(title, kind, source=None, unit=None, n=24):
    lid = db.execute("INSERT INTO word_lists (title, created_at, kind, level_id,"
                     " source, unit) VALUES (?,?,?,?,?,?)",
                     (title, now, kind, lv["Pre-Intermediate"], source, unit)).lastrowid
    for i in range(n):
        opts = json.dumps(["wrong%da" % i, "wrong%db" % i, "wrong%dc" % i])
        db.execute("INSERT INTO words (list_id, term, translation, options, ord)"
                   " VALUES (?,?,?,?,?)", (lid, "term%d" % i, "right%d" % i, opts, i))
    return lid

# two books of vocabulary, and a grammar ladder
e1 = [mklist("Essential Words 1 · Unit %d" % u, "vocab", "4000 Essential Words 1", str(u))
      for u in (1, 2, 3)]
e2 = [mklist("Essential Words 2 · Unit %d" % u, "vocab", "4000 Essential Words 2", str(u))
      for u in (1, 2)]
gr = [mklist("Present simple", "grammar"), mklist("Past simple", "grammar"),
      mklist("Present perfect", "grammar")]
db.commit()

print("1. THE PASS MARK IS 18 OF 20")
print("   a round is %d questions, pass mark %d" % (core.SOLO_ROUND, core.pass_mark(core.SOLO_ROUND)))
assert core.SOLO_ROUND == 20 and core.pass_mark(20) == 18
assert core.pass_mark(10) == 9 and core.pass_mark(24) == 22
print("   a shorter list keeps the same 90%: 9 of 10, 22 of 24")

print("\n2. VOCABULARY IS FILED BY BOOK")
books = core.play_books(db, me, "vocab")
print("   books:", [(b["title"], b["steps"], b["passed"]) for b in books])
assert [b["title"] for b in books] == ["4000 Essential Words 1", "4000 Essential Words 2"]
assert [b["steps"] for b in books] == [3, 2]

print("\n3. ONLY STEP ONE IS OPEN AT THE START")
chain = core.play_chain(db, me, "grammar")
print("   grammar:", [(c["step"], c["list"]["title"], "open" if c["unlocked"] else "locked")
                      for c in chain])
assert [c["unlocked"] for c in chain] == [True, False, False]
assert core.can_play(db, me, gr[0]) and not core.can_play(db, me, gr[1])

def play(lid, right):
    """Play a round, getting `right` of them correct."""
    rid = core.start_solo(db, me, lid)
    assert rid, "the round was refused"
    st = core.solo_state(db, rid, sid)
    n = 0
    while st["state"] == "question":
        want = db.execute("SELECT translation FROM words WHERE id="
                          "(SELECT word_id FROM solo_questions WHERE run_id=? AND ord=?)",
                          (rid, st["q"])).fetchone()["translation"]
        pos = st["options"].index(want)
        core.answer_solo(db, rid, sid, st["q"], pos if n < right else (pos + 1) % 4)
        n += 1
        st = core.solo_state(db, rid, sid)
    return st

print("\n4. A NEAR MISS DOES NOT UNLOCK")
st = play(gr[0], 17)
print("   17 of 20 -> passed: %s (needed %d)" % (st["passed"], st["need"]))
assert st["passed"] is False
assert not core.can_play(db, me, gr[1]), "17 of 20 opened the next step"
print("   step 2 is still locked")

print("\n5. EIGHTEEN PASSES, AND OPENS THE NEXT STEP")
st = play(gr[0], 18)
print("   18 of 20 -> passed: %s" % st["passed"])
assert st["passed"] is True
chain = core.play_chain(db, me, "grammar")
assert [c["passed"] for c in chain] == [True, False, False]
assert [c["unlocked"] for c in chain] == [True, True, False]
print("   step 2 is open, step 3 is not")

print("\n6. THE LOCK IS ON THE SERVER, NOT ONLY ON THE PAGE")
srv = server.Server(("127.0.0.1", 8819), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
time.sleep(0.4)
B = "http://127.0.0.1:8819"
op = urllib.request.build_opener()
r = op.open(B + "/s/%s/solo/start" % tok, urllib.parse.urlencode({"list": gr[2]}).encode(),
            timeout=20)
assert r.geturl().endswith("tab=play"), "a locked step could be started from the address bar"
print("   starting step 3 from the address bar is refused")
page = op.open(B + "/s/%s?tab=play&l=%d" % (tok, gr[2]), timeout=20).read().decode()
assert "locked" in page and "Past simple" in page
print("   and its page says which step must be passed first")

print("\n7. THE BOOKS ARE SEPARATE LADDERS")
assert core.can_play(db, me, e1[0]) and core.can_play(db, me, e2[0])
assert not core.can_play(db, me, e1[1])
print("   unit 1 of each book is open; unit 2 waits for unit 1 of its own book")
play(e1[0], 24)
assert core.can_play(db, me, e1[1]), "passing book 1 unit 1 did not open unit 2"
assert not core.can_play(db, me, e2[1]), "it opened a step in the other book"
print("   passing book 1 unit 1 opens book 1 unit 2, and nothing in book 2")

print("\n8. A PASSED STEP STAYS PASSED")
old = core.week_start()
d2 = core.connect()
d2.execute("UPDATE solo_runs SET finished_at=? WHERE list_id=?",
           (core.iso(core.parse(old) - __import__("datetime").timedelta(days=30)), gr[0]))
d2.commit(); d2.close()
assert core.can_play(db, me, gr[1]), "a step passed last month was taken back"
print("   a step passed a month ago still holds the next one open")
srv.shutdown()
print("\nPASS  Play is a career: books, steps, 18 of 20, and no way to skip one")
