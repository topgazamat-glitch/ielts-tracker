"""Anonymous lesson ratings — see the assertions for what it guarantees.

Run me with:  python3 run_tests.py            (all of them)
              python3 tests/rating_test.py   (just this one)
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
core.init_db(); db = core.connect(); cfg = core.load_config()
now = core.iso(core.now()); today = core.local_day(core.now(), cfg)
g = db.execute("INSERT INTO groups (name, join_code, created_at) VALUES ('214','AA',?)", (now,)).lastrowid
toks = []
for i, name in enumerate(("Shirin", "Bek", "Nodira", "Aziz")):
    sid = db.execute("INSERT INTO students (name, group_id, active, token, created_at)"
                     " VALUES (?,?,1,?,?)", (name, g, "tok%016d" % i, now)).lastrowid
    toks.append((sid, "tok%016d" % i))
    db.execute("INSERT INTO lesson_marks (student_id, day, punctuality, behaviour, participation,"
               " created_at) VALUES (?,?,4,4,4,?)", (sid, today, now))
db.commit(); db.close()

srv = server.Server(("127.0.0.1", 8840), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start(); time.sleep(0.4)
B = "http://127.0.0.1:8840"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(B + "/login", urllib.parse.urlencode({"password": "testpw123"}).encode()).read()
def student(tok, tab):
    return urllib.request.urlopen(B + "/s/%s?tab=%s" % (tok, tab), timeout=30).read().decode("utf-8")
def rate(tok, day, scores, keep="", change=""):
    d = dict(scores); d.update({"day": day, "keep": keep, "change": change})
    r = urllib.request.urlopen(B + "/s/%s/rate" % tok, urllib.parse.urlencode(d).encode(), timeout=30)
    return r.geturl().split("rated=")[-1]
five = {k: 5 for k, _l, _h in core.RATING_ASPECTS}
mixed = {"atmosphere": 5, "clarity": 4, "learning": 4, "pace": 2, "involvement": 3, "feedback": 4}

print("1. THE PAGE PROMISES ANONYMITY, AND THE TABLE KEEPS IT")
pg = student(toks[0][1], "home")
print("   the home tab asks after today's lesson:", "How was today" in pg)
assert "How was today" in pg
pg = student(toks[0][1], "rate")
print("   six aspects, five stars each:", pg.count('class="stars"') == 6 and pg.count("&#9733;") == 30)
assert pg.count('class="stars"') == 6
print("   says it is anonymous and how:", "Anonymous" in pg and str(core.MIN_RATERS) in pg)
assert "Anonymous" in pg
cols = [r[1] for r in core.connect().execute("PRAGMA table_info(lesson_ratings)")]
print("   the ratings table has no student column at all:", "student_id" not in cols, cols)
assert "student_id" not in cols

print("\n2. RATING, ONCE PER LESSON")
print("   Shirin rates today:", rate(toks[0][1], today, mixed, keep="the group work", change="slower on grammar"))
assert rate(toks[0][1], today, mixed) == "already"
print("   a second go the same day is refused: already")
print("   half a form is refused:", rate(toks[1][1], today, {"atmosphere": 5}) == "bad")
print("   a lesson from the future is refused:", rate(toks[1][1], "2999-01-01", five) == "bad")
pg = student(toks[0][1], "home")
print("   the nudge is gone once rated:", "How was today" not in pg)
assert "How was today" not in pg
pg = student(toks[0][1], "rate")
print("   today reads as rated in the picker:", "Today - rated" in pg)
assert "Today - rated" in pg

print("\n3. THE TEACHER SEES NOTHING UNTIL THREE HAVE RATED")
t = op.open(B + "/lessons").read().decode("utf-8")
print("   one rating: hidden, and says why:", "waiting for classmates" in t and "the group work" not in t)
assert "the group work" not in t and "waiting for classmates" in t
rate(toks[1][1], today, five, keep="examples on the board")
t = op.open(B + "/lessons").read().decode("utf-8")
print("   two ratings: still hidden:", "the group work" not in t)
assert "the group work" not in t
rate(toks[2][1], today, {"atmosphere": 4, "clarity": 5, "learning": 5, "pace": 3, "involvement": 5, "feedback": 5},
     change="more speaking")
t = op.open(B + "/lessons").read().decode("utf-8")
print("   three ratings: shown, with the comments and no names:",
      "the group work" in t and "more speaking" in t and "Shirin" not in t and "Nodira" not in t)
assert "the group work" in t and "more speaking" in t and "Shirin" not in t
print("   strongest and weakest named:", "Strongest:" in t and "To work on:" in t)
assert "Strongest:" in t and "To work on:" in t
agg = core.lesson_ratings(core.connect(), g)
by = {a["key"]: a["avg"] for a in agg["aspects"]}
print("   pace is the weak one:", by["pace"], "| atmosphere:", by["atmosphere"])
assert by["pace"] < by["atmosphere"] and agg["n"] == 3
print("   the week table has this week:", core.week_key(today) in t)
assert core.week_key(today) in t
pg = student(toks[3][1], "rate")
print("   students see their class's bars too:", "How your class rated" in pg)
assert "How your class rated" in pg

print("\n4. A STUDENT WHO LEAVES TAKES ONLY THEIR TICKET")
db = core.connect()
before = db.execute("SELECT COUNT(*) c FROM lesson_ratings").fetchone()["c"]
core.remove_student(db, toks[0][0])
after = db.execute("SELECT COUNT(*) c FROM lesson_ratings").fetchone()["c"]
tickets = db.execute("SELECT COUNT(*) c FROM rating_tickets WHERE student_id=?", (toks[0][0],)).fetchone()["c"]
print("   ratings kept:", before == after == 3, "| ticket gone:", tickets == 0)
assert before == after == 3 and tickets == 0
db.close()

srv.shutdown(); shutil.rmtree(tmp)
print("\nThe students can say it; the teacher can hear it; nobody can trace it.")
