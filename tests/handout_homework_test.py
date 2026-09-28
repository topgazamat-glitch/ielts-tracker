"""A digital handout set as homework: opened for one class with a deadline,
marked by itself, averaged with the teacher's marks into the league.

Run me with:  python3 run_tests.py handout_homework
"""
import html as _html
import http.cookiejar
import json
import os
import re
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
import core, server, bot

core.init_db(); db = core.connect(); cfg = core.load_config()
now = core.iso(core.now())
core.start_season(db, core.now() - timedelta(days=20))
lvl = db.execute("SELECT id FROM levels WHERE name='Pre-Intermediate'").fetchone()["id"]
g1 = db.execute("INSERT INTO groups (name, join_code, created_at, level_id) VALUES ('214','A',?,?)",
                (now, lvl)).lastrowid
g2 = db.execute("INSERT INTO groups (name, join_code, created_at, level_id) VALUES ('215','B',?,?)",
                (now, lvl)).lastrowid
ann = core.add_student(db, "Anvar", g1)
bek = core.add_student(db, "Bekzod", g1)
cam = core.add_student(db, "Kamola", g2)
tok = {sid: db.execute("SELECT token FROM students WHERE id=?", (sid,)).fetchone()["token"]
       for sid in (ann, bek, cam)}

TEAL = core.BOOKLET_TEAL


def bar(n, name):
    return ('<table class="bk"><tr><td style="background:#%s"><p><span>%d</span></p></td>'
            '<td><p><span>%s</span></p></td></tr></table>' % (TEAL, n, name))


def ex(label, text):
    return ('<p><span style="font-weight:700;color:#%s;font-size:12pt">%s  </span>'
            '<span>%s</span></p>' % (TEAL, label, text))


def box(n):
    return '<input class="bk-blank" data-q="%d" style="width:60px">' % n


layout = ('<div class="booklet">' + bar(1, "Reading · a text")
          + ex("1.1", "Which day?") + '<p data-item="1.1:1"><span>1  </span><span>' + box(1) + '</span></p>'
          + '<p data-item="1.1:2"><span>2  </span><span>Go ' + box(2) + '</span></p>'
          + ex("1.2", "Why?") + '<p data-item="1.2:1"><span>1  </span><span>' + box(3) + '</span></p>'
          + bar(2, "Listening · a talk")
          + ex("2.1", "Listen.") + '<p data-item="2.1:1"><span>1  </span><span>' + box(4) + '</span></p>'
          + "</div>")
DAY = [{"letter": d, "text": "Day " + d} for d in "123"]


def handout(title, published):
    tid = core.load_test(db, {
        "level": "Pre-Intermediate", "number": 2, "title": title, "kind": "handout",
        "layout": layout, "passages": {}, "questions": [
            {"num": 1, "kind": "typed", "prompt": "1.1  1", "answer": "1", "options": DAY},
            {"num": 2, "kind": "typed", "prompt": "1.1  2", "answer": "went"},
            {"num": 3, "kind": "open", "prompt": "1.2  1 Why?", "answer": None, "control": "long"},
            {"num": 4, "kind": "typed", "prompt": "2.1  1", "answer": "slept"}]})
    db.execute("UPDATE dtests SET published=? WHERE id=?", (1 if published else 0, tid))
    db.commit()
    return tid


hid = handout("Unit 2 — Homework version", False)       # opens only when set
practice = handout("Unit 2 — Practice", True)            # open to the whole level
Q = {r["num"]: r["id"] for r in db.execute("SELECT id, num FROM dquestions WHERE test_id=?", (hid,))}

fails, checks = [], 0


def check(what, cond):
    global checks
    checks += 1
    print(("  ok  " if cond else "  FAIL") + "  " + what)
    if not cond:
        fails.append(what)


srv = server.Server(("127.0.0.1", 8844), server.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
time.sleep(0.4)
base = "http://127.0.0.1:8844"
jar = http.cookiejar.CookieJar()
teacher = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
teacher.open(base + "/login", urllib.parse.urlencode({"password": "pw"}).encode()).read()
op = urllib.request.build_opener()


def tget(path):
    return _html.unescape(teacher.open(base + path, timeout=20).read().decode())


def get(path):
    return _html.unescape(op.open(base + path, timeout=20).read().decode())


def post(path, fields):
    return json.loads(op.open(base + path, urllib.parse.urlencode(fields).encode(),
                              timeout=20).read().decode())


print("1. SETTING IT")
pg = tget("/assignments")
check("the form offers the handouts, under their level",
      'name="handout"' in pg and '<optgroup label="Pre-Intermediate"' in pg)
check("one not open as practice says it opens only for the class",
      "Unit 2 — Homework version (opens only for this class)" in pg)
due = core.local_day(core.now() + timedelta(days=2), cfg)
teacher.open(base + "/assignments/list", urllib.parse.urlencode({
    "group_id": g1, "items": "Workbook unit 2 A & C", "handout": hid, "due": due,
    "due_time": "18:00", "publish": "1"}).encode()).read()
rows = db.execute("SELECT * FROM assignments WHERE group_id=? ORDER BY id", (g1,)).fetchall()
check("the workbook and the handout are one set, one deadline",
      len(rows) == 2 and rows[0]["due_at"] == rows[1]["due_at"] and rows[1]["test_id"] == hid)
hw = rows[1]

print("\n2. WHO CAN OPEN IT")
check("the class it was set to has it on its Handouts page",
      "Unit 2 — Homework version" in get("/s/%s?tab=handouts" % tok[ann]))
check("another class at the same level does not",
      "Unit 2 — Homework version" not in get("/s/%s?tab=handouts" % tok[cam]))
check("and cannot open it by its address",
      "That booklet is not open" in get("/s/%s?tab=handouts&h=%d" % (tok[cam], hid)))
check("or save into it", post("/s/%s/handout/%d/save" % (tok[cam], hid), {"q%d" % Q[1]: "1"}).get("ok") is False)
check("the practice handout stays open to everyone",
      "Unit 2 — Practice" in get("/s/%s?tab=handouts" % tok[cam]))

print("\n3. ON THE STUDENT'S HOMEWORK")
home = get("/s/%s?tab=home" % tok[ann])
check("it is on the list, with a way in", "Unit 2 — Homework version" in home
      and "tab=handouts&h=%d" % hid in home and "0/2 parts" in home)
check("it is not something to send a photograph for",
      not re.search(r'<option value="%d">' % hw["id"], home)
      and 'name="assignment_id" value="%d"' % hw["id"] not in home)
check("nor in the bot", hw["id"] not in [a["id"] for a in bot.open_assignments(db, g1)])
page = get("/s/%s?tab=handouts&h=%d" % (tok[ann], hid))
check("the handout says it is homework, and when it is due", "hwstrip" in page and "due " in page)

print("\n4. A WRITTEN ANSWER NEEDS A FEW WORDS")
out = post("/s/%s/handout/%d/check" % (tok[ann], hid),
           {"part": "1", "q%d" % Q[1]: "1", "q%d" % Q[2]: "go", "q%d" % Q[3]: "x"})
check("'x' is not an answer", out.get("ok") is False and 3 in out.get("missing", []))
check("the box says so to the page", 'data-min-words="3"' in page)
out = post("/s/%s/handout/%d/check" % (tok[ann], hid),
           {"part": "1", "q%d" % Q[1]: "1", "q%d" % Q[2]: "go", "q%d" % Q[3]: "Because it was quiet"})
check("three words are", out.get("ok") is True)

print("\n5. THE MARK: HALF FOR DOING IT, HALF FOR GETTING IT RIGHT")
st = core.handout_status(db, hid, ann, hw["due_at"])
# 1 of 2 parts: 2.5; right answers 1 of 2 (the listening's one is not counted): 2.5
check("one part of two, one of two right: 5 out of 10", st["parts"] == 1 and st["mark"] == 5.0)
check("the listening is not in the right-answers half",
      len([q for q, p in core.handout_info(db, hid)["marked"].items() if p != 2]) == 2)
home = get("/s/%s?tab=home" % tok[ann])
check("the Homework list shows how far they are", "1/2 parts" in home)

# the deadline passes; then the second part is checked, too late to count
past = core.iso(core.now() - timedelta(minutes=1))
db.execute("UPDATE dparts SET checked_at=? WHERE part=1", (core.iso(core.now() - timedelta(hours=1)),))
db.execute("UPDATE assignments SET due_at=? WHERE group_id=?", (past, g1)); db.commit()
post("/s/%s/handout/%d/check" % (tok[ann], hid), {"part": "2", "q%d" % Q[4]: "slept"})
st = core.handout_status(db, hid, ann, past)
check("a part checked after the deadline does not count", st["parts"] == 1 and st["mark"] == 5.0)
check("the page says what is done now is practice",
      "what you do now is practice" in get("/s/%s?tab=handouts&h=%d" % (tok[ann], hid)))

print("\n6. INTO THE LEAGUE, AVERAGED WITH THE TEACHER'S MARK")
wb = db.execute("SELECT id FROM assignments WHERE group_id=? AND test_id IS NULL", (g1,)).fetchone()["id"]
db.execute("INSERT INTO submissions (student_id, assignment_id, status, score, created_at, kind)"
           " VALUES (?,?,'graded',8,?,'photo')",
           (ann, wb, core.iso(core.now() - timedelta(hours=2))))
db.commit()


def points(sid):
    r = next(x for x in core.championship(db)["rows"] if x["student"]["id"] == sid)
    return r["points"].get("homework", 0)


check("workbook 8 and handout 5 average 6.5: 1.95 points", abs(points(ann) - 1.95) < 0.01)
check("nothing done by the deadline scores nought, like missing homework", points(bek) == 0)
db.execute("INSERT INTO submissions (student_id, assignment_id, status, score, created_at, kind)"
           " VALUES (?,?,'graded',6,?,'photo')", (bek, wb, core.iso(core.now() - timedelta(hours=2))))
db.commit()
check("so Bekzod's workbook 6 with no handout is 0.9", abs(points(bek) - 0.9) < 0.01)
stats = core.student_stats(db, ann)
check("the handout is handed in on the student's record, with its mark",
      any(t.get("handout") and t["score"] == 5.0 for t in stats["timeline"]) and stats["completion"] == 100)
check("and counts towards the live completion rate", core.live_completion(db, ann) == 100)

print("\n7. THE TEACHER'S VIEW")
setpg = tget("/homework/set?group=%d&due=%s" % (g1, urllib.parse.quote(past)))
check("the grid shows the handout's mark", 'title="1 of 2 parts, 5 out of 10">5</span>' in setpg)
check("and where to read what they wrote", "/tests/%d/writing" % hid in setpg)
wr = tget("/tests/%d/writing" % hid)
check("the writing page has their answer, and a way to void it",
      "Because it was quiet" in wr and "does not count" in wr)
att = db.execute("SELECT id FROM dattempts WHERE test_id=? AND student_id=?", (hid, ann)).fetchone()["id"]
teacher.open(base + "/tests/%d/void" % hid, urllib.parse.urlencode(
    {"attempt": att, "question": Q[3], "on": "1"}).encode()).read()
st = core.handout_status(db, hid, ann, past)
check("a voided answer takes its part out of 'done'", st["parts"] == 0 and st["voided"] == 1)
check("the right answers in it still count: 2.5", st["mark"] == 2.5)
teacher.open(base + "/tests/%d/void" % hid, urllib.parse.urlencode(
    {"attempt": att, "question": Q[3], "on": "0"}).encode()).read()
check("and it can be counted after all", core.handout_status(db, hid, ann, past)["mark"] == 5.0)

print("\n8. PRACTICE EARNS NOTHING; LAST WEEK'S HOMEWORK CAN BE SET AGAIN")
before = points(ann)
pq = {r["num"]: r["id"] for r in db.execute("SELECT id, num FROM dquestions WHERE test_id=?", (practice,))}
post("/s/%s/handout/%d/check" % (tok[ann], practice),
     {"part": "1", "q%d" % pq[1]: "1", "q%d" % pq[2]: "went", "q%d" % pq[3]: "It was very quiet"})
check("a practice handout does not touch the league", points(ann) == before)
r = teacher.open(base + "/groups/%d/repeat" % g1, urllib.parse.urlencode(
    {"due": core.local_day(core.now() + timedelta(days=9), cfg), "due_time": "18:00"}).encode())
again = db.execute("SELECT COUNT(*) c, SUM(test_id IS NOT NULL) h FROM assignments WHERE group_id=?",
                   (g1,)).fetchone()
check("'repeat last homework' works, handout and all", r.status == 200 and again["c"] == 4 and again["h"] == 2)

srv.shutdown()
print()
print("handout_homework: %d checks, %d failed" % (checks, len(fails)))
sys.exit(1 if fails else 0)
